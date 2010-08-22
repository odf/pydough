import math


class Mesh(object):
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


class Subgeometry(object):
    def __init__(self, base, indices):
        self.verts   = base.verts
        self.tverts  = base.tverts
        self.normals = base.normals

        self.mesh = Mesh([base.polys[i] for i in indices])
        
        if base.tpolys:
            self.tmesh = Mesh([base.tpolys[i] for i in indices])

    def fix_texture_seams(self):
        used = self.mesh.used_indices
        polygons = self.mesh.polys
        tpolygons = self.tmesh.polys

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
                             for x in self.tverts[self.tmesh.used_indices[tv]]])
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
        mesh = self.mesh
        tmesh = self.tmesh
        nr_verts = len(mesh.used_indices)
        
        corner_to_tex = [None] * nr_verts
        corner_from_tex = {}
        
        for i, p in enumerate(mesh.polys):
            for j, v in enumerate(p):
                if corner_to_tex[v] is None:
                    tv = tmesh.polys[i][j]
                    corner_to_tex[v] = tv
                    corner_from_tex[tv] = v

        tmesh.used_indices = [tmesh.used_indices[i] for i in corner_to_tex]
        for i, p in enumerate(tmesh.polys):
            tmesh.polys[i] = [corner_from_tex[v] for v in p]

    def write(self, file):
        if self.tverts:
            self.fix_texture_seams()
            self.reorder_tex_verts()
        
        print >>file, 'Shape "mesh"'
        if self.mesh.polys:
            print >>file, ' "integer triindices" ['
            for poly in self.mesh.polys:
                for v in xrange(1, len(poly) - 1):
                    print >>file, poly[0], poly[v], poly[v + 1]
            print >>file, ']\n'

        fmt2d = "%.8f %.8f"
        fmt3d = "%.8f %.8f %.8f"

        verts = self.verts
        if verts and self.mesh.used_indices:
            print >>file, ' "point P" ['
            for i in self.mesh.used_indices:
                print >>file, fmt3d % tuple(verts[i])
            print >>file, ']\n'

        normals = self.normals
        if normals and self.mesh.used_indices:
            print >>file, ' "normal N" ['
            for i in self.mesh.used_indices:
                print >>file, fmt3d % tuple(normals[i])
            print >>file, ']\n'

        tverts = self.tverts
        if tverts and self.tmesh.used_indices:
            print >>file, ' "float uv" ['
            for i in self.tmesh.used_indices:
                print >>file, fmt2d % tuple(tverts[i])
            print >>file, ']\n'
