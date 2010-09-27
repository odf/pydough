print "Loading ", __name__

import math
import Numeric as num

from geometry import Geometry


def normalize(rows):
    norms = num.sqrt(num.maximum(num.sum(rows * rows, 1), 1e-16))
    return rows / norms[:, num.NewAxis]

def cross(u, v):
    return num.array([u[1]*v[2] - u[2]*v[1],
                      u[2]*v[0] - u[0]*v[2],
                      u[0]*v[1] - u[1]*v[0]])

def make_fiber(verts_in, r_start = 0.01, r_end = 0.01, gon = 5):
    n = len(verts_in)
    directions = normalize(num.subtract(verts_in[1:], verts_in[:-1]))
    bisectors = normalize(num.add(directions[1:], directions[:-1]))

    d = directions[0]
    if abs(num.dot(d, [1,0,0])) > 0.9:
        u = cross(d, [0,1,0])
    else:
        u = cross(d, [1,0,0])
    v = cross(d, u)
    u, v = normalize(num.array([u, v]))
    a = 2 * math.pi / gon

    section = num.array([u * math.cos(a * i) + v * math.sin(a * i)
                         for i in xrange(gon)])

    verts_out = num.zeros([n * gon, 3], "double")
    normals   = num.zeros([n * gon, 3], "double")
    verts_out[:gon] = section * r_start + verts_in[0]
    normals[:gon]   = section

    for i in xrange(n - 2):
        d = bisectors[i]
        u = directions[i]
        f = num.sum(section * d, 1)[:, num.NewAxis]
        section = section - f / num.dot(d, u) * u
        r = ((i + 1) * r_end + (n - i - 1) * r_start) / n
        verts_out[(i + 1)*gon : (i + 2)*gon] = section * r + verts_in[i + 1]
        normals[(i + 1)*gon : (i + 2)*gon]   = section

    d = directions[-1]
    section = section - num.sum(section * d, 1)[:, num.NewAxis] * d
    verts_out[-gon:] = section * r_end + verts_in[-1]
    normals[-gon:]   = section

    return verts_out, normalize(normals), fiber_polygons(n - 1, gon)

def fiber_polygons(n, m):
    polys = [None] * (2 + n * m)
    ring = num.zeros([m, 4], "int")
    for i in xrange(m):
        i1 = (i + 1) % m
        ring[i] = [i, i1, i1 + m, i + m]
    for k in xrange(0, n * m, m):
        polys[k : k + m] = (ring + k).tolist()
    polys[-2] = range(m-1, -1, -1)
    polys[-1] = range(n * m, (n + 1) * m)

    return polys


class HairGeometry(Geometry):
    def compute(self):
        if hasattr(self, '_processed'):
            return

        r_root = self.options.get('root_radius', 0.0001)
        r_tip  = self.options.get('tip_radius', 0.00004)
        hair_verts     = num.zeros([0,3], "double")
        hair_normals   = num.zeros([0,3], "double")
        hair_tverts    = num.zeros([0,2], "double")
        hair_polys     = []
        hair_poly_mats = []
        for p, t, m in map(None, self.polys, self.tpolys, self.poly_mats):
            new_verts, new_normals, new_polys = make_fiber(num.take(self.verts, p),
                                                           r_root, r_tip)
            offset = len(hair_verts)
            hair_polys.extend([[v + offset for v in p] for p in new_polys])
            hair_poly_mats.extend([m] * len(new_polys))
            hair_verts   = num.concatenate([hair_verts, new_verts])
            hair_normals = num.concatenate([hair_normals, new_normals])
            hair_tverts  = num.concatenate(
                [hair_tverts, [self.tverts[t[0]]] * len(new_verts)])

        options = dict(self.options.items() + [('skip_check', True)])
        self._processed = Geometry(hair_verts, hair_polys, hair_poly_mats,
                                   hair_normals, hair_tverts,
                                   [p[:] for p in hair_polys], options)

    def check_tpolys(self):
        pass

    def gon(self):
        return 5
    gon = property(gon)

    def number_of_normals(self):
        return self.number_of_points
    number_of_normals = property(number_of_normals)

    def number_of_points(self):
        return len(self.verts or []) * self.gon
    number_of_points = property(number_of_points)

    def number_of_polygons(self):
        m = self.gon
        return (2 - m) * len(self.polys or []) + self.number_of_points
    number_of_polygons = property(number_of_polygons)

    def number_of_texture_points(self):
        return len(self.tverts or []) * self.gon
    number_of_texture_points = property(number_of_texture_points)

    def triangles(self):
        self.compute()
        for poly in (self._processed.polys or []):
            for v in xrange(1, len(poly) - 1):
                yield poly[0], poly[v], poly[v + 1]
    triangles = property(triangles)

    def points(self):
        self.compute()
        for v in (self._processed.verts or []):
            yield tuple(v)
    points = property(points)

    def normals(self):
        self.compute()
        for n in (self._processed._normals or []):
            yield tuple(n)
    normals = property(normals)

    def texture_points(self):
        self.compute()
        for v in (self._processed.tverts or []):
            yield tuple(v)
    texture_points = property(texture_points)
