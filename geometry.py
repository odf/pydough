print "Loading ", __name__

import Numeric as num


class Geometry(object):
    def __init__(self, verts, polys, poly_mats = None, normals = None,
                 tverts = None, tpolys = None):
        self.verts     = verts
        self.polys     = polys
        self.poly_mats = poly_mats
        self.normals   = normals
        self.tverts    = tverts
        self.tpolys    = tpolys

        self.polys_at_vert = pav = [[] for v in self.verts]
        for i, poly in enumerate(self.polys):
            for v in poly:
                pav[v].append(i)

    def compute_normals(self):
        rotate = lambda v: num.take(v, [1,2,0], 1)
        
        p_indices = num.concatenate(self.polys)
        q_indices = num.concatenate([p[1:] + p[:1] for p in self.polys])

        ends = num.add.accumulate([len(p) for p in self.polys])
        starts = num.concatenate([[0], ends])
        sets = [range(a,o) for a, o in zip(starts, ends)]

        p = num.take(self.verts, p_indices)
        q = num.take(self.verts, q_indices)
        cross = rotate(p * rotate(q) - q * rotate(p))

        normals = num.array([num.sum(num.take(cross, s)) for s in sets])
        norms = num.sqrt(num.maximum(num.sum(normals * normals, 1), 1e-16))
        self.face_normals = fnormals = normals / norms[:, num.NewAxis]

        normals = num.array([num.sum(num.take(fnormals, s))
                             for s in self.polys_at_vert])
        norms = num.sqrt(num.maximum(num.sum(normals * normals, 1), 1e-16))
        self.normals = normals / norms[:, num.NewAxis]

    def compute_normals_slower(self):
        """
        Alternative function for computing the vertex normals, Slower,
        but slightly less cryptic.
        """
        rotate  = lambda v: num.take(v, [1,2,0], 1)
        verts   = self.verts
        normals = num.zeros([len(verts), 3], "double")

        for indices in self.polys:
            p = num.take(verts, indices)
            q = num.take(verts, indices[1:] + indices[:1])
            n = num.sum(p * rotate(q) - q * rotate(p))
            n = n / num.sqrt(num.maximum(num.dot(n, n), 1e-16))

            for v in indices: normals[v] += n

        norms = num.sqrt(num.maximum(num.sum(normals * normals, 1), 1e-16))
        self.normals = rotate(normals) / norms[:, num.NewAxis]

    def interpolate(self, center, adj):
        self.verts[center] = num.sum(num.take(self.verts, adj)) / len(adj)
        if self.normals:
            n = num.sum(num.take(self.normals, adj))
            self.normals[center] = n / num.sqrt(num.maximum(num.dot(n, n),
                                                                1e-16))

    def subdivide(self):
        # -- grab some instance data
        verts   = self.verts
        normals = self.normals
        
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
        if normals:
            self.normals = normals = num.resize(normals, (new_size, 3))

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
