import os.path, profile

import geometry_export
reload(geometry_export)
import geometry_export

path = geometry_export.findMyFolder()
profile.run('geometry_export.exportScene()', os.path.join(path, 'profile.stat'))
