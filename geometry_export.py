print "Loading ", __name__

import geometry, poser_extractor
reload(geometry)
reload(poser_extractor)

from poser_extractor import extract_geometry


class GeometryExporter(object):
    def __init__(self, subject, convert_material = None,
                 write_mesh_parameters = None, options = {}):

        self.convert_material = convert_material or (
            lambda mat, key: ' NamedMaterial "%s/%s"' % (key, mat.Name())
        )
        self.write_mesh_parameters = write_mesh_parameters
        self.options = options

        self.geom = extract_geometry(subject)
        if self.geom is None or self.geom.is_empty:
            print "Mesh is empty."
        else:
            print "Mesh has", self.geom.number_of_polygons, "polygons and",
            print self.geom.number_of_points, "vertices"
            self.preprocess(options)

    def preprocess(self, options):
        self.materials = [self.convert_material(mat, self.geom.material_key)
                          for mat in self.geom.materials]
        do_normals = options.get('compute_normals', True)
        if do_normals and not do_normals in ['0', 'false', 'False']:
            self.geom.compute_normals()
        for i in xrange(int(options.get('subdivisionlevel', 0))):
            print "  subdividing: pass", (i+1)
            self.geom.subdivide()
        self.geom.convert_to_per_vertex_uvs()

    def write_submesh(self, file, sub):
        print >>file, 'Shape "mesh"'
        if self.write_mesh_parameters:
            self.write_mesh_parameters(file, sub, self.options) 

        print >>file, ' "integer triindices" ['
        for u, v, w in sub.triangles: print >>file, u, v, w
        print >>file, ']\n'

        print >>file, ' "point P" ['
        for x, y, z in sub.points: print >>file, x, y, z
        print >>file, ']\n'

        if sub.number_of_normals:
            print >>file, ' "normal N" ['
            for x, y, z in sub.normals: print >>file, x, y, z
            print >>file, ']\n'

        if sub.number_of_texture_points:
            print >>file, ' "float uv" ['
            for u, v in sub.texture_points: print >>file, u, v
            print >>file, ']\n'

    def write(self, file):
        if self.geom.is_empty:
            return
        
        for i, mat in enumerate(self.materials):
            sub = self.geom.extract_by_material(i)
            if not sub.is_empty:
                print >>file, 'AttributeBegin'
                print >>file, mat
                self.write_submesh(file, sub)
                print >>file, 'AttributeEnd\n'
