print "Loading ", __name__

import geometry, hair, from_poser, to_lux
reload(geometry)
reload(hair)
reload(from_poser)
reload(to_lux)
import from_poser, to_lux


def get_materials(geometry, convert = None):
    f = convert or (lambda mat, k: ' NamedMaterial "%s/%s"' % (k, mat.Name()))
    return [f(mat, geometry.material_key) for mat in geometry.materials]


def preprocess(geometry, options = {}):
    if options.get('compute_normals', True) in [True, 1, '1', 'true']:
        geometry.compute_normals()
    for i in xrange(int(options.get('subdivisionlevel', 0))):
        print "  subdividing: pass", (i+1)
        geometry.subdivide()


class GeometryExporter(object):
    def __init__(self, subject, convert_material = None,
                 write_mesh_parameters = None, options = {}):

        geom = from_poser.get(subject)
        if geom is None or geom.is_empty:
            print "Mesh is empty."
            self.write = lambda file: None
        else:
            print "Mesh has %s polygons and %s vertices" % (
                geom.number_of_polygons, geom.number_of_points)

            materials = get_materials(geom, convert_material)
            preprocess(geom, options)
            self.write = lambda file: to_lux.write(file, geom, materials,
                                                   write_mesh_parameters)


def findMyFolder():
    # return the folder containing this script
    import sys, os.path
    return os.path.dirname(findMyFolder.func_code.co_filename)

def exportScene(output = None, options = {}):
    import poser
    
    if not output:
        import os.path
        print "Using default output path."
        output = file(os.path.join(findMyFolder(), "test.lxo"), "w")

    scene = poser.Scene()
    for figure in scene.Figures():
        if figure.Visible():
            GeometryExporter(figure, options = options).write(output)
    for actor in scene.Actors():
        if actor.Visible() and actor.IsProp():
            GeometryExporter(actor, options = options).write(output)
