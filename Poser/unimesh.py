import Numeric as num

def topological_order(children):
    seen = {}
    result = []

    def visit(v):
        if not seen.has_key(v):
            seen[v] = True
            for w in children[v]: visit(w)
            result.insert(0, v)

    is_child = {}
    for v in children.keys():
        for w in children[v]:
            is_child[w] = True
    
    for v in children.keys():
        if not is_child.has_key(v):
            visit(v)

    return result


class WeldingInfo(object):
    def __init__(self, figure):
        self.figure = figure
        self.collect_info()

    def welding_order(self):
        after = {}
        for actor in self.figure.Actors():
            after.setdefault(actor.Name(), [])
            for goal in actor.WeldGoalActors():
                after.setdefault(goal.Name(), []).append(actor.Name())
        return topological_order(after)

    def collect_info(self):
        good_actor = lambda a: a.Geometry() and a.Visible()
        figure = self.figure

        self.map_vertex  = map_vertex = {}
        self.new_vertex  = new_vertex = {}
        self.map_tvertex = map_tvertex = {}
        self.new_tvertex = new_tvertex = {}

        count = 0
        tcount = 0

        for name in self.welding_order():
            actor = figure.Actor(name)
            if not good_actor(actor): continue

            nv = actor.Geometry().NumVertices()
            a_map = map_vertex[name] = [None] * nv
            a_new = new_vertex[name] = [False] * nv
            
            for goal, new_map in zip(actor.WeldGoalActors(), actor.WeldGoals()):
                if not good_actor(goal): continue
                g_map = map_vertex[goal.Name()]
                for v, w in enumerate(new_map):
                    if w >= 0: a_map[v] = g_map[w]

            for v in xrange(nv):
                if a_map[v] is None:
                    a_map[v] = count
                    a_new[v] = True
                    count += 1

            nt = actor.Geometry().NumTexVertices()
            map_tvertex[name] = [i + tcount for i in xrange(nt)]
            new_tvertex[name] = [True] * nt
            tcount += nt

        self.used_actors = [a for a in figure.Actors() if good_actor(a)]
        self.vertex_count = count
        self.tvertex_count = tcount


class Unimesh(object):
    def __init__(self, figure):
        self.figure = figure
        self.collect_data()
        
    def convert_materials_for_figure(self, actors):
        material_key = self.figure.Name()
        material_index = {}
        map_material = {}
        materials = []
        for actor in actors:
            a_name = actor.Name()
            for i, mat in enumerate(actor.Geometry().Materials()):
                m_name = mat.Name()
                if not material_index.has_key(m_name):
                    material_index[m_name] = len(materials)
                    materials.append(mat)
                map_material[(a_name, i)] = material_index[m_name]

        return materials, map_material

    def collect_data(self):
        print "Converting figure %s to a single mesh:" % self.figure.Name()

        welding_info = WeldingInfo(self.figure)
        actors = welding_info.used_actors
        nr_verts = welding_info.vertex_count
        nr_tverts = welding_info.tvertex_count
        nr_polys = sum([len(actor.Geometry().Polygons())
                        for actor in actors])
        nr_tpolys = sum([len(actor.Geometry().TexPolygons())
                         for actor in actors])

        print ("  %d vertices in welded vs %d in unwelded figure"
               % (nr_verts, sum([a.Geometry().NumVertices() for a in actors])))

        materials, map_material = self.convert_materials_for_figure(actors)
        self.materials = materials
        print "  %d listed materials" % len(materials)

        self.verts     = verts     = num.zeros([nr_verts, 3], "double")
        self.tverts    = tverts    = num.zeros([nr_tverts, 2], "double")
        self.polys     = polys     = [None] * nr_polys
        self.poly_mats = poly_mats = [None] * nr_polys
        self.tpolys    = tpolys    = [None] * nr_tpolys

        pcount  = 0
        tpcount = 0 

        for actor in actors:
            name = actor.Name()
            geom = actor.Geometry()
            sets = geom.Sets()
            tsets = geom.TexSets()

            new_vert = welding_info.new_vertex[name]
            map_vert = welding_info.map_vertex[name]
            for i, v in enumerate(geom.WorldVertices()):
                if new_vert[i]:
                    verts[map_vert[i]] = [v.X(), v.Y(), v.Z()]

            for p in geom.Polygons():
                start = p.Start()
                indices = sets[start : start + p.NumVertices()]
                polys[pcount] = [map_vert[v] for v in indices]
                poly_mats[pcount] = map_material[(name, p.MaterialIndex())]
                pcount += 1

            if geom.TexVertices():
                new_tvert = welding_info.new_tvertex[name]
                map_tvert = welding_info.map_tvertex[name]
                for i, v in enumerate(geom.TexVertices()):
                    if new_tvert[i]:
                        tverts[map_tvert[i]] = [v.U(), v.V()]

                for p in geom.TexPolygons():
                    start = p.Start()
                    indices = tsets[start : start + p.NumTexVertices()]
                    tpolys[tpcount] = [map_tvert[v] for v in indices]
                    tpcount += 1
        print
