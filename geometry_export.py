print "Loading ", __name__

import poser_extractor
reload(poser_extractor)
from poser_extractor import extract_mesh

import geometry
reload(geometry)
from geometry import Geometry, TopologyError


class GeometryExporter(object):
    def __init__(self, subject, convert_material = None, options = {}):
        mesh = extract_mesh(subject)
        self.materials = mesh.materials
        self.mat_key = mesh.material_key
        self.convert_material = convert_material or (
            lambda mat, key: "# " + mat.Name())

        if mesh.polys:
            self.geom = Geometry(mesh.verts, mesh.polys, mesh.poly_mats,
                                 None, mesh.tverts, mesh.tpolys)
            if options.get('compute_normals', True):
                self.geom.compute_normals()
            for i in xrange(int(options.get('subdivisionlevel', 0))):
                self.geom.subdivide()
        else:
            self.geom = None

    def write_submesh(self, file, sub):
        print >>file, 'Shape "mesh"'

        print >>file, ' "integer triindices" ['
        for u, v, w in sub.triangles: print >>file, u, v, w
        print >>file, ']\n'

        print >>file, ' "point P" ['
        for x, y, z in sub.points: print >>file, x, y, z
        print >>file, ']\n'

        if sub.has_normals:
            print >>file, ' "normal N" ['
            for x, y, z in sub.normals: print >>file, x, y, z
            print >>file, ']\n'

        if sub.has_texture_points:
            print >>file, ' "float uv" ['
            for u, v in sub.texture_points: print >>file, u, v
            print >>file, ']\n'

    def write(self, file):
        if not self.geom: return
        
        for mat_idx, mat in enumerate(self.materials):
            indices = [i for i,n in enumerate(self.geom.poly_mats)
                       if n == mat_idx]
            if not indices: continue

            print >>file, 'AttributeBegin'
            print >>file, self.convert_material(mat, self.mat_key)
            try:
                sub = self.geom.selection(indices)
                sub.convert_to_per_vertex_uvs()
                self.write_submesh(file, sub)
            except TopologyError, message:
                print "WARNING: In", mat.Name(), "-", message
            print >>file, 'AttributeEnd\n'
