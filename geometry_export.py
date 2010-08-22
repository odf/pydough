import poser
import Numeric as num

from Poser.unimesh import Unimesh
from geometry import Subgeometry


class GeometryExporter(object):
    def __init__(self, actor_or_figure, material_converter = None, options = {}):
        self.convert_material = material_converter or (
            lambda mat, key: "# Material \'%s/%s\'" % (key, mat.Name()))
        
        if isinstance(actor_or_figure, poser.ActorType):
            self.actor = actor_or_figure
            self.figure = self.actor.ItsFigure()
            self.get_data_from_actor()
        elif isinstance(actor_or_figure, poser.FigureType):
            self.figure = actor_or_figure
            self.get_data_from_unimesh()
        else:
            raise RuntimeError("Argument must be an actor or figure.")

        if not self.empty:
            self.compute_normals()
            for i in xrange(options.get('subdivisionlevel', 0)):
                self.subdivide()

    def get_data_from_actor(self):
        geom = self.actor.Geometry()
        self.empty = not (geom and self.actor.Visible())
        if self.empty: return

        sets = geom.Sets()
        tsets = geom.TexSets()

        self.verts = num.array([[v.X(), v.Y(), v.Z()]
                                for v in geom.WorldVertices()], 'd')
        self.polys = [sets[p.Start() : p.Start() + p.NumVertices()]
                      for p in geom.Polygons()]
        self.poly_mats = [p.MaterialIndex()
                          for p in geom.Polygons()]
        if geom.TexVertices():
            self.tverts = num.array([[v.U(), v.V()]
                                     for v in geom.TexVertices()], 'd')
            self.tpolys = [tsets[p.Start() : p.Start() + p.NumTexVertices()]
                           for p in geom.TexPolygons()]
        else:
            self.tverts = self.tpolys = []

        if self.figure:
            key = self.figure.Name()
        else:
            key = self.actor.Name()
        self.materials = [self.convert_material(mat, key)
                          for mat in geom.Materials()]

    def get_data_from_unimesh(self):
        unimesh = Unimesh(self.figure)

        self.empty     = False
        self.verts     = unimesh.verts
        self.tverts    = unimesh.tverts
        self.polys     = unimesh.polys
        self.poly_mats = unimesh.poly_mats
        self.tpolys    = unimesh.tpolys

        key = self.figure.Name()
        self.materials = [self.convert_material(mat, key)
                          for mat in unimesh.materials]
        
    def compute_normals(self):
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

    def write(self, file):
        if self.empty: return
        
        for mat_idx, material in enumerate(self.materials):
            indices = [i for i,n in enumerate(self.poly_mats) if n == mat_idx]

            if indices:
                print >>file, 'AttributeBegin'
                print >>file, material
                Subgeometry(self, indices).write(file)
                print >>file, 'AttributeEnd\n'
