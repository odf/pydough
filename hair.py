print "# Loading ", __name__

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
    verts_out[:gon] = section * r_start + verts_in[0]

    for i in xrange(n - 2):
        d = bisectors[i]
        u = directions[i]
        f = num.sum(section * d, 1)[:, num.NewAxis]
        section = section - f / num.dot(d, u) * u
        r = ((i + 1) * r_end + (n - i - 1) * r_start) / n
        verts_out[(i + 1)*gon : (i + 2)*gon] = section * r + verts_in[i + 1]

    d = directions[-1]
    section = section - num.sum(section * d, 1)[:, num.NewAxis] * d
    verts_out[-gon:] = section * r_end + verts_in[-1]

    return verts_out, fiber_polygons(n - 1, gon)

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
    def __init__(self, verts, polys, poly_mats = None, normals = None,
                 tverts = None, tpolys = None, options = {}):
        r_root = options.get('root_radius', 0.0001)
        r_tip  = options.get('tip_radius', 0.00004)
        hair_verts = num.zeros([0,3], "double")
        hair_polys = []
        hair_poly_mats = []
        for p, m in map(None, polys, poly_mats):
            new_verts, new_polys = make_fiber(num.take(verts, p), r_root, r_tip)
            n = len(hair_verts)
            hair_polys.extend([[v + n for v in p] for p in new_polys])
            hair_poly_mats.extend([m] * len(new_polys))
            hair_verts = num.concatenate([hair_verts, new_verts])

        Geometry.__init__(self, hair_verts, hair_polys, hair_poly_mats)


if __name__ == "__main__":
    verts, polys = make_fiber([[1,0,0],[0,1,1],[-1,2,0],[0,3,-1],[1,4,0]],
                              0.2, 0.1)
    for x,y,z in verts: print "v", x, y, z
    for p in polys:
        print "f", " ".join(map(lambda i: str(i + 1), p))
