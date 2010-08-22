import Numeric as num

from topology import Topology


def compute_welding(points, tolerance):
    keys = num.floor(num.array(points) / tolerance + 0.5).astype(num.Int)

    vertex_at = {}
    remap = {}
    for v, k in enumerate(keys):
        key = tuple(k)
        w = vertex_at.get(key)
        if w:
            remap[v] = w
        else:
            vertex_at[key] = v
    return remap


class Mesh(object):
    def __init__(self, points, polygons, normals = None,
                 tex_points = None, tex_polygons = None, options = {}):
        self.points  = points
        self.tpoints = tex_points
        self.normals = normals

        self.construct_topologies(polygons, tex_polygons)

    def construct_topologies(self, polygons, tex_polygons):
        geo_remap = tex_remap = None

        tolerance = options.get('weld_vertices', 0)
        if tolerance > 0: geo_remap = compute_welding(self.tpoints, tolerance)

        if tex_polygons:
            self._topology          = geo = Topology()
            self._tex_topology      = tex = Topology()
            self._halfedge_to_tex   = to  = {}
            self._halfedge_from_tex = fro = {}

            tolerance = options.get('weld_textures', 1e-5)
            if tolerance > 0: tex_remap = compute_welding(self.points, tolerance)

            for poly, tpoly in map(None, polygons, tex_polygons):
                if geo_remap: poly = [geo_remap.get(v, v) for v in poly]
                geo.add_polygon(poly)
                
                if tex_remap: tpoly = [tex_remap.get(v, v) for v in tpoly]
                tex.add_polygon(tpoly)

                for (u, v, s, t) in map(None, poly, poly[1:] + poly[:1],
                                        tpoly, tpoly[1:] + tpoly[:1]):
                    to[(u, v)]  = (s, t)
                    fro[(s, t)] = (u, v)
        else:
            self._topology = geo = Topology()
            for poly in polygons:
                if geo_remap: poly = [geo_remap.get(v, v) for v in poly])
                geo.add_polygon(poly)

            self._tex_topology = None
