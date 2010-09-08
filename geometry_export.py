print "Loading ", __name__

import geometry, from_poser, to_lux
reload(geometry)
reload(from_poser)
reload(to_lux)
import from_poser, to_lux


class GeometryExporter(object):
    def __init__(self, subject, convert_material = None,
                 write_mesh_parameters = None, options = {}):

        geom = from_poser.get(subject)
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

            if options.get('compute_normals', True) in [True, 1, '1', 'true']:
                geom.compute_normals()
            for i in xrange(int(options.get('subdivisionlevel', 0))):
                print "  subdividing: pass", (i+1)
                geom.subdivide()
            to_lux.preprocess(geom)

            self.write = lambda file: to_lux.write(file, geom, materials,
                                                   write_mesh_parameters)
