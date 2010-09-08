print "Loading ", __name__

def to_lux(file, geometry, materials, write_mesh_parameters = None):
    if geometry.is_empty:
        return
        
    for i, mat in enumerate(materials):
        sub = geometry.extract_by_material(i)
        if not sub.is_empty:
            print >>file, 'AttributeBegin'
            print >>file, mat
            print >>file, 'Shape "mesh"'
            if write_mesh_parameters:
                write_mesh_parameters(file, sub)

            print >>file, ' "integer triindices" ['
            for u, v, w in sub.triangles: print >>file, u, v, w
            print >>file, ']\n'

            print >>file, ' "point P" ['
            for x, y, z in sub.points: print >>file, x, y, z
            print >>file, ']\n'

            if sub.number_of_normals:
                print >>file, ' "normal N" ['
                for x, y, z in sub.normals: print >>file, x, y, z
                print >>file, ']\n'

            if sub.number_of_texture_points:
                print >>file, ' "float uv" ['
                for u, v in sub.texture_points: print >>file, u, v
                print >>file, ']\n'
            print >>file, 'AttributeEnd\n'
