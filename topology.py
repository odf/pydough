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
        
        self._polygons = []
        self._vertices = {}
        self._halfedge = {}
        self._opposite = {}

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
        
        index = len(self._polygons)
        size = len(polygon)

        for i, v, w in zip(xrange(size), polygon, polygon[1:] + polygon[:1]):
            this = (index, i)
            if self._halfedge.has_key((v, w)):
                raise TopologyError("The same oriented edge occurred twice.")
            else:
                self._halfedge[(v, w)] = this
            other = self._halfedge.get((w, v), None)
            self._opposite[this] = other
            if other:
                self._opposite[other] = this

        self._polygons.append(polygon[:])

        for v in polygon:
            self._vertices[v] = True
