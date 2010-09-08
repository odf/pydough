print "Loading ", __name__

import geometry, poser_extractor, to_lux
reload(geometry)
reload(poser_extractor)
reload(to_lux)

from poser_extractor import extract_geometry
from to_lux import to_lux


class GeometryExporter(object):
    def __init__(self, subject, convert_material = None,
                 write_mesh_parameters = None, options = {}):

        geom = extract_geometry(subject)
        if geom is None or geom.is_empty:
            print "Mesh is empty."
            self.write = lambda file: None
        else:
            print "Mesh has", geom.number_of_polygons, "polygons and",
            print geom.number_of_points, "vertices"

            mats = geom.materials
            key = geom.material_key
            if convert_material:
                materials = [convert_material(mat, key) for mat in mats]
            else:
                materials = [' NamedMaterial "%s/%s"' % (key, mat.Name())
                             for mat in mats]

            do_normals = options.get('compute_normals', True)
            if do_normals and not do_normals in ['0', 'false', 'False']:
                geom.compute_normals()
            for i in xrange(int(options.get('subdivisionlevel', 0))):
                print "  subdividing: pass", (i+1)
                geom.subdivide()
            geom.convert_to_per_vertex_uvs()

            self.write = lambda file: to_lux(file, geom, materials,
                                             write_mesh_parameters)
