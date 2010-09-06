print "Loading ", __name__

import poser_extractor
reload(poser_extractor)
from poser_extractor import extract_mesh

import geometry
reload(geometry)
from geometry import Geometry, TopologyError


class GeometryExporter(object):
    def __init__(self, subject, convert_material = None,
                 write_mesh_parameters = None, options = {}):
        self.convert_material = convert_material or (
            lambda mat, key: "# " + mat.Name())
        self.write_mesh_parameters = write_mesh_parameters
        self.options = options

        mesh = extract_mesh(subject)
        self.materials = mesh.materials
        self.mat_key = mesh.material_key

        if mesh.polys:
            self.geom = Geometry(mesh.verts, mesh.polys, mesh.poly_mats,
                                 None, mesh.tverts, mesh.tpolys)
            print "Mesh has", len(self.geom.polys), "polygons and",
            print len(self.geom.tpolys), "texture polygons"

            do_normals = options.get('compute_normals', True)
            if do_normals and not do_normals in ['0', 'false', 'False']:
                self.geom.compute_normals()
            for i in xrange(int(options.get('subdivisionlevel', 0))):
                print "  subdividing: pass", (i+1)
                self.geom.subdivide()
        else:
            self.geom = None

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
            sub = self.geom.extract_by_material(mat_idx)
            if sub.is_empty: continue

            print >>file, 'AttributeBegin'
            print >>file, self.convert_material(mat, self.mat_key)
            sub.convert_to_per_vertex_uvs()
            self.write_submesh(file, sub)
            print >>file, 'AttributeEnd\n'
