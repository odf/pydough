print "Loading ", __name__

import math


class Topology(object):
    def __init__(self, polys):
        self.polys        = []
        self.index_map    = imap = {}
        self.used_indices = used = []

        self.polys = [None] * len(polys)
        for i, poly in enumerate(polys):
            for v in poly:
                if not imap.has_key(v):
                    imap[v] = len(used)
                    used.append(v)

            self.polys[i] = [imap[v] for v in poly]


class Submesh(object):
    def __init__(self, base, indices):
        self.message = None
        self._verts   = base.verts
        self._normals = base.normals
        self._tverts  = None

        self._topology = Topology([base.polys[i] for i in indices])
        
        if not base.tpolys: return

        if len(base.tpolys) != len(base.polys):
            self.message = "Incorrect number of texture polygons."
            return
        
        for i in indices:
            if len(base.tpolys[i]) != len(base.polys[i]):
                self.message = "Texture polygon of incorrect size."
                return

        self._tverts  = base.tverts
        self._tex_topology = Topology([base.tpolys[i] for i in indices])
        self.fix_texture_seams()
        self.reorder_tex_verts()

    def fix_texture_seams(self):
        used      = self._topology.used_indices
        tused     = self._tex_topology.used_indices
        polygons  = self._topology.polys
        tpolygons = self._tex_topology.polys

        corners_by_vertex = {}
        for v in xrange(len(used)):
            corners_by_vertex[v] = []
            
        for i, poly in enumerate(polygons):
            for j, v in enumerate(poly):
                corners_by_vertex[v].append((i, j))

        for v, corners_for_v in corners_by_vertex.items():
            tverts = [tpolygons[i][j] for i,j in corners_for_v]
            tverts.sort()
            if tverts[0] == tverts[-1]:
                continue
            
            original_vertex = used[v]

            by_tvert = {}
            for i, j in corners_for_v:
                by_tvert.setdefault(tpolygons[i][j], []).append((i, j))

            by_texture_position = {}
            for tv in by_tvert.keys():
                key = tuple([int(math.floor(x * 5000 + 0.5))
                             for x in self._tverts[tused[tv]]])
                by_texture_position.setdefault(key, []).append(tv)

            remap = {}
            for colliding in by_texture_position.values():
                for tv in colliding:
                    remap[tv] = colliding[0]

            for i, j in corners_for_v:
                tpolygons[i][j] = remap[tpolygons[i][j]]

            by_tvert = {}
            for i, j in corners_for_v:
                by_tvert.setdefault(tpolygons[i][j], []).append((i, j))
            for tv, corners_for_tv in by_tvert.items()[1:]:
                new_v = len(used)
                used.append(original_vertex)
                for i, j in corners_for_tv:
                    polygons[i][j] = new_v

    def reorder_tex_verts(self):
        topology     = self._topology
        tex_topology = self._tex_topology
        nr_verts     = len(topology.used_indices)
        
        corner_to_tex = [None] * nr_verts
        corner_from_tex = {}
        
        for i, p in enumerate(topology.polys):
            for j, v in enumerate(p):
                if corner_to_tex[v] is None:
                    tv = tex_topology.polys[i][j]
                    corner_to_tex[v] = tv
                    corner_from_tex[tv] = v

        tex_topology.used_indices = [tex_topology.used_indices[i]
                                     for i in corner_to_tex]
        for i, p in enumerate(tex_topology.polys):
            tex_topology.polys[i] = [corner_from_tex[v] for v in p]

    def is_empty(self):
        return not self._topology.polys
    is_empty = property(is_empty)

    def has_normals(self):
        return self._normals and self._topology.used_indices
    has_normals = property(has_normals)

    def has_texture_points(self):
        return self._tverts and self._tex_topology.used_indices
    has_texture_points = property(has_texture_points)

    def triangles(self):
        for poly in self._topology.polys:
            for v in xrange(1, len(poly) - 1):
                yield poly[0], poly[v], poly[v + 1]
    triangles = property(triangles)

    def points(self):
        for i in self._topology.used_indices:
            yield tuple(self._verts[i])
    points = property(points)

    def normals(self):
        for i in self._topology.used_indices:
            yield tuple(self._normals[i])
    normals = property(normals)

    def texture_points(self):
        for i in self._tex_topology.used_indices:
            yield tuple(self._tverts[i])
    texture_points = property(texture_points)
