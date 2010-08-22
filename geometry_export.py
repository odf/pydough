print "Loading ", __name__

import poser
import Numeric as num

from Poser.unimesh import Unimesh

import geometry
reload(geometry)
from geometry import Geometry

import submesh
reload(submesh)
from submesh import Submesh


class GeometryExporter(Geometry):
    def __init__(self, actor_or_figure, material_converter = None, options = {}):
        self.convert_material = material_converter or (
            lambda mat, key: "# Material \'%s/%s\'" % (key, mat.Name()))
        
        if isinstance(actor_or_figure, poser.ActorType):
            self.actor = actor_or_figure
            self.figure = self.actor.ItsFigure()
            data = self.get_data_from_actor()
        elif isinstance(actor_or_figure, poser.FigureType):
            self.figure = actor_or_figure
            data = self.get_data_from_unimesh()
        else:
            raise RuntimeError("Argument must be an actor or figure.")

        verts, polys, poly_mats, tverts, tpolys, self.materials = data
        Geometry.__init__(self, verts, polys, poly_mats, None, tverts, tpolys)

        self.empty = not self.polys

        if not self.empty:
            if options.get('compute_normals', True):
                self.compute_normals()
            for i in xrange(options.get('subdivisionlevel', 0)):
                self.subdivide()

    def get_data_from_actor(self):
        geom = self.actor.Geometry()
        if not (geom and self.actor.Visible()):
            return [None] * 6

        sets = geom.Sets()
        tsets = geom.TexSets()

        verts = num.array([[v.X(), v.Y(), v.Z()]
                           for v in geom.WorldVertices()], 'd')
        polys = [sets[p.Start() : p.Start() + p.NumVertices()]
                 for p in geom.Polygons()]
        poly_mats = [p.MaterialIndex() for p in geom.Polygons()]
        if geom.TexVertices():
            tverts = num.array([[v.U(), v.V()]
                                for v in geom.TexVertices()], 'd')
            tpolys = [tsets[p.Start() : p.Start() + p.NumTexVertices()]
                      for p in geom.TexPolygons()]
        else:
            tverts = tpolys = []

        if self.figure:
            key = self.figure.Name()
        else:
            key = self.actor.Name()
        materials = [self.convert_material(mat, key)
                     for mat in geom.Materials()]

        return verts, polys, poly_mats, tverts, tpolys, materials

    def get_data_from_unimesh(self):
        uni = Unimesh(self.figure)
        key = self.figure.Name()
        materials = [self.convert_material(mat, key) for mat in uni.materials]

        return (uni.verts, uni.polys, uni.poly_mats,
                uni.tverts, uni.tpolys, materials)

    def write_submesh(self, file, sub):
        print >>file, 'Shape "mesh"'

        print >>file, ' "integer triindices" ['
        for u, v, w in sub.triangles:
            print >>file, u, v, w
        print >>file, ']\n'

        print >>file, ' "point P" ['
        for x, y, z in sub.points:
            print >>file, "%.8f %.8f %.8f" % (x, y, z)
        print >>file, ']\n'

        if sub.has_normals:
            print >>file, ' "normal N" ['
            for nx, ny, nz in sub.normals:
                print >>file, "%.8f %.8f %.8f" % (nx, ny, nz)
            print >>file, ']\n'

        if sub.has_texture_points:
            print >>file, ' "float uv" ['
            for u, v in sub.texture_points:
                print >>file, "%.8f %.8f" % (u, v)
            print >>file, ']\n'

    def write(self, file):
        if self.empty: return
        
        for mat_idx, material in enumerate(self.materials):
            indices = [i for i,n in enumerate(self.poly_mats) if n == mat_idx]

            if indices:
                print >>file, 'AttributeBegin'
                print >>file, material
                self.write_submesh(file, Submesh(self, indices))
                print >>file, 'AttributeEnd\n'
