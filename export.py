import poser

import gui.tk_background, gui.main, geometry_export
reload(gui.tk_background)
reload(gui.main)
reload(geometry_export)
import gui.main
from geometry_export import exportScene

gui.main.go(exportScene)
