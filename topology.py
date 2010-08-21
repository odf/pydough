"""
This package contains classes and methods concerned with the topology
of a mesh.
"""

class TopologyError(RuntimeError):
    def __init__(self, str):
        RuntimeError.__init__(self, str)


class Topology(object):
    """
    This class captures the topology, or in other words, the
    relationships between the vertices, edges and polygons, of a
    mesh. Geometric and material information such a vertex positions,
    normals and uv coordinates for textures are not included.
    """
    
    def __init__(self, polygons = []):
        """
        The initializer accepts an initial list of polygons which is
        then passed to the add_polygons() method.
        """
        
        self._polygons           = []
        self._vertex_to_halfedge = {}
        self._next_halfedge      = {}

        self.add_polygons(polygons)

    def add_polygons(self, polygons):
        """
        Adds a number of polygons by passing each one to the
        add_polygon() method.
        """
        
        for polygon in polygons:
            self.add_polygon(polygon)

    def add_polygon(self, polygon):
        """
        Adds a single polygon to the mesh topology, which must be
        given as an array of vertex identifiers (usually indices, but
        any hashable object will do).
        """
        
        vertices = polygon + polygon[:2]

        for i in xrange(len(polygon)):
            u, v, w = vertices[i : i+3]
            if self._next_halfedge.has_key((u, v)):
                raise TopologyError("The same oriented edge occurred twice.")
            else:
                self._next_halfedge[(u, v)] = (v, w)
            self._vertex_to_halfedge[u] = (u, v)
            
        self._polygons.append(polygon[:])

    def polygons(self):
        for poly in self._polygons:
            yield poly[:]
    polygons = property(polygons)

    def vertices(self):
        for v in self._vertex_to_halfedge.keys():
            yield v
    vertices = property(vertices)

    def next_in_polygon(self, v, w):
        return self._next_halfedge[(v, w)]

    def neighbor_vertices(self, v):
        _, w = self._vertex_to_halfedge[v]
        first = w
        while True:
            yield w
            _, w = self._next_halfedge[(w, v)]
            if w == first: break

    def on_boundary(self, v, w):
        return not self._next_halfedge.has_key((w, v))
