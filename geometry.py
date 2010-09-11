print "Loading ", __name__

import math
import Numeric as num


def normalize(rows):
    norms = num.sqrt(num.maximum(num.sum(rows * rows, 1), 1e-16))
    return rows / norms[:, num.NewAxis]


class SubmeshData(object):
    def __init__(self, verts, polys):
        self.used  = list(dict([(v, True) for p in polys for v in p]))
        vmap = dict(zip(self.used, xrange(len(self.used))))
        self.polys = [[vmap[v] for v in p] for p in polys]
        self.verts = num.take(verts, self.used)


class Geometry(object):
    def __init__(self, verts, polys, poly_mats = None, normals = None,
                 tverts = None, tpolys = None, options = {}):
        self.verts     = verts
        self.polys     = polys
        self.poly_mats = poly_mats
        self._normals  = normals
        self.tverts    = tverts
        self.tpolys    = tpolys

        self.log = options.get('logger', self.default_logger)

        if self.tpolys and self.tverts:
            if len(self.polys) != len(self.tpolys):
                self.tverts = self.tpolys = None
                self.log("Corrupted UVs removed.")
            else:
                count = 0
                for poly, tpoly in zip(self.polys, self.tpolys):
                    if len(tpoly) != len(poly):
                        count += 1
                        if len(tpoly) == 0:
                            tpoly.append(0)
                        while len(tpoly) < len(poly):
                            tpoly.append(tpoly[-1])

                if count: self.log(count, "bad UV polygons")

    def default_logger(self, *args):
        print " ".join(map(str, args))

    def extract_by_material(self, material_index):
        return self.extract([i for i, n in enumerate(self.poly_mats or [])
                             if n == material_index])

    def extract(self, poly_indices):
        geomesh = SubmeshData(self.verts, [self.polys[i] for i in poly_indices])
        poly_mats = [self.poly_mats[i] for i in poly_indices]
        if self._normals:
            normals = num.take(self._normals, geomesh.used)
        else:
            normals = None

        if self.tpolys and self.tverts:
            texmesh = SubmeshData(self.tverts,
                                  [self.tpolys[i] for i in poly_indices])
            geom = Geometry(geomesh.verts, geomesh.polys, poly_mats, normals,
                            texmesh.verts, texmesh.polys)
            return geom
        else:
            return Geometry(geomesh.verts, geomesh.polys, poly_mats, normals)

    def compute_normals(self):
        rotate = lambda v: num.take(v, [1,2,0], 1)
        
        p = num.take(self.verts, num.concatenate(self.polys))
        q = num.take(self.verts, num.concatenate([poly[1:] + poly[:1]
                                                  for poly in self.polys]))
        cross = rotate(p * rotate(q) - q * rotate(p))

        ends    = num.add.accumulate([len(p) for p in self.polys])
        starts  = num.concatenate([[0], ends])
        normals = num.array([num.sum(num.take(cross, range(a,o)))
                             for a, o in zip(starts, ends)])
        self.face_normals = fnormals = normalize(normals)

        normals = num.zeros([len(self.verts), 3], "double")
        for i, poly in enumerate(self.polys):
            n = fnormals[i]
            for v in poly: normals[v] += n
        self._normals = normalize(normals)

    def interpolate(self, center, adj):
        self.verts[center] = num.sum(num.take(self.verts, adj)) / len(adj)
        if self._normals:
            n = num.sum(num.take(self._normals, adj))
            self._normals[center] = n / num.sqrt(num.maximum(num.dot(n, n),
                                                             1e-16))

    def subdivide(self):
        # -- grab some instance data
        verts   = self.verts
        normals = self._normals
        
        original_polys        = self.polys
        original_poly_mats    = self.poly_mats
        original_vertex_count = len(verts)
        
        # -- holds next available vertex index
        next_index = len(verts)

        # -- count edges and assign vertex indices for edge centers
        edge_centers  = {}
        edge_center_to_poly_centers = {}
        vertex_to_edge_centers = [[] for v in xrange(original_vertex_count)]

        for poly in original_polys:
            for u, v in zip(poly, poly[1:] + poly[:1]):
                if edge_centers.has_key((v, u)):
                    ec = edge_centers[(u, v)] = edge_centers[(v, u)]
                else:
                    ec = edge_centers[(u, v)] = next_index
                    next_index += 1
                    edge_center_to_poly_centers[ec] = []
                    vertex_to_edge_centers[u].append(ec)
                    vertex_to_edge_centers[v].append(ec)

        # -- make room for edge and polygon centers in vertex arrays
        new_size = next_index + len(original_polys)
        self.verts = verts = num.resize(verts, (new_size, 3))
        if self._normals:
            self._normals = normals = num.resize(normals, (new_size, 3))

        # -- create the polygon centers and new polygons
        vertex_to_poly_centers = [[] for v in xrange(original_vertex_count)]

        self.polys     = polys     = []
        self.poly_mats = poly_mats = []

        for i, poly in enumerate(original_polys):
            if len(poly) < 1: continue

            # -- claim next free vertex index
            center = next_index
            next_index += 1

            # -- interpolate 3d and texture coordinates and normals
            self.interpolate(center, poly)

            # -- get the edge centers on the polygon's boundary
            ecs = [edge_centers[(u, v)]
                   for u, v in zip(poly, poly[1:] + poly[:1])]

            # -- subdivide the polygon
            mat = original_poly_mats[i]
            
            for u, v, w in zip(ecs[-1:] + ecs[:-1], poly, ecs):
                polys.append([u, v, w, center])
                poly_mats.append(mat)
                vertex_to_poly_centers[v].append(center)

            # -- link edge centers to new polygon center
            for ec in ecs:
                edge_center_to_poly_centers[ec].append(center)

        # -- subdivide the texture polygons
        if self.tverts:
            tverts  = self.tverts
            n = len(tverts)
            tverts_needed = n + sum([1 + len(tpoly) for tpoly in self.tpolys])
            self.tverts = tverts = num.resize(tverts, (tverts_needed, 2))
        
            original_tpolys = self.tpolys
            self.tpolys = tpolys = []

            for i, poly in enumerate(original_tpolys):
                nv = len(poly)
                if nv < 1: continue
                ecs = range(n, n+nv)
                for u, v in zip(poly, poly[1:] + poly[:1]):
                    tverts[n] = (tverts[u] + tverts[v]) / 2
                    n += 1
                tverts[n] = num.sum(num.take(tverts, ecs)) / nv
                for u, v, w in zip(ecs[-1:] + ecs[:-1], poly, ecs):
                    tpolys.append([u, v, w, n])
                n += 1

        # -- flag border vertices
        on_border = [False] * len(verts)
        for (u,v), ec in edge_centers.items():
            if len(edge_center_to_poly_centers[ec]) == 1:
                on_border[u] = on_border[v] = on_border[ec] = True

        # -- adjust edge center positions
        for (u, v), ec in edge_centers.items():
            if u > v and edge_centers.has_key((v, u)): continue
            if on_border[ec]:
                self.interpolate(ec, [u, v])
            else:
                self.interpolate(ec, [u, v] + edge_center_to_poly_centers[ec])

        # -- adjust positions of original vertices
        for v in xrange(original_vertex_count):
            ecs = vertex_to_edge_centers[v]
            pcs = vertex_to_poly_centers[v]
            k = len(ecs)

            if k < 2: continue
            
            if on_border[v]:
                self.interpolate(v, [u for u in ecs if on_border[u]])
            else:
                a = num.sum(num.take(verts, ecs)) * 4 / k
                b = num.sum(num.take(verts, pcs)) / k
                verts[v] = (verts[v] * (k - 3) + a - b) / k

    def convert_to_per_vertex_uvs(self):
        if self.tpolys and self.tverts:
            self.fix_texture_seams()
            self.reorder_tex_verts()

    def corners_by_vertex(self):
        result = [[] for v in self.verts]
        for i, poly in enumerate(self.polys):
            for j, v in enumerate(poly):
                result[v].append((i, j))
        return result

    def fix_texture_seams(self):
        polygons  = self.polys
        tpolygons = self.tpolys
        corners   = self.corners_by_vertex()

        indices = range(len(self.verts))
        for v, corners_for_v in enumerate(corners):
            by_tvert = dict([(tpolygons[i][j], True) for i, j in corners_for_v])
            if len(by_tvert) < 2:
                continue

            by_texture_position = {}
            for tv in by_tvert:
                key = tuple([int(x * 5000) for x in self.tverts[tv]])
                by_texture_position.setdefault(key, []).append(tv)

            remap = {}
            for colliding in by_texture_position.values():
                for tv in colliding:
                    remap[tv] = colliding[0]

            for i, j in corners_for_v: tpolygons[i][j] = remap[tpolygons[i][j]]

            by_tvert = {}
            for i, j in corners_for_v:
                by_tvert.setdefault(tpolygons[i][j], []).append((i, j))

            for tv, corners_for_tv in by_tvert.items()[1:]:
                for i, j in corners_for_tv:
                    polygons[i][j] = len(indices)
                indices.append(v)

        self.verts = num.take(self.verts, indices)
        if self._normals: self._normals = num.take(self._normals, indices)

    def reorder_tex_verts(self):
        tpolys = self.tpolys
        corner_to_tex = [None] * len(self.verts)
        corner_from_tex = {}
        
        for i, p in enumerate(self.polys):
            for j, v in enumerate(p):
                if corner_to_tex[v] is None:
                    tv = tpolys[i][j]
                    corner_to_tex[v] = tv
                    corner_from_tex[tv] = v

        self.tverts = num.take(self.tverts, corner_to_tex)
        self.tpolys = [[corner_from_tex[v] for v in p] for p in tpolys]

    def is_empty(self):
        return (self.number_of_points == 0) or (self.number_of_polygons == 0)
    is_empty = property(is_empty)

    def number_of_normals(self):
        return len(self._normals or [])
    number_of_normals = property(number_of_normals)

    def number_of_points(self):
        return len(self.verts or [])
    number_of_points = property(number_of_points)

    def number_of_polygons(self):
        return len(self.polys or [])
    number_of_polygons = property(number_of_polygons)

    def number_of_texture_points(self):
        return len(self.tverts or [])
    number_of_texture_points = property(number_of_texture_points)

    def triangles(self):
        for poly in (self.polys or []):
            for v in xrange(1, len(poly) - 1):
                yield poly[0], poly[v], poly[v + 1]
    triangles = property(triangles)

    def points(self):
        for v in (self.verts or []):
            yield tuple(v)
    points = property(points)

    def normals(self):
        for n in (self._normals or []):
            yield tuple(n)
    normals = property(normals)

    def texture_points(self):
        for v in (self.tverts or []):
            yield tuple(v)
    texture_points = property(texture_points)
