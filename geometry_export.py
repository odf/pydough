print "Loading ", __name__

import os.path

from portability import *
import geometry, hair, from_poser, to_lux
reload(geometry)
reload(hair)
reload(from_poser)
reload(to_lux)
import from_poser, to_lux
from hair import HairGeometry


def is_set(options, key, default = True):
    return options.get(key, default) in [True, 1, '1', 'true']

def get_materials(geom, convert = None):
    f = convert or (lambda mat, k: ' NamedMaterial "%s/%s"' % (k, mat.Name()))
    return [f(mat, geom.material_key) for mat in geom.materials]

def preprocess(geom, options = {}):
    if not isinstance(geom, HairGeometry):
        if is_set(options, 'compute_normals'):
            print "  computing normals"
            geom.compute_normals()
        for i in xrange(int(options.get('subdivisionlevel', 0))):
            print "  subdividing: pass", (i+1)
            geom.subdivide()


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
    import inspect
    import portability
    return os.path.dirname(inspect.getsourcefile(portability))


def exportScene(output = None, options = {}):
    import time
    import poser
    
    if not output:
        filename = os.path.join(findMyFolder(), "test.lxo")
        output = file(filename, "w")
        print "Exporting to %s..." % filename

    t = time.time()

    scene = poser.Scene()
    for figure in scene.Figures():
        if figure.Visible():
            GeometryExporter(figure, options = options).write(output)
    for actor in scene.Actors():
        if actor.Visible() and actor.IsProp():
            GeometryExporter(actor, options = options).write(output)

    t = time.time() - t
    print "Time spent was %.2f seconds." % t


if __name__ == "__main__":
    exportScene()
