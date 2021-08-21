# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
	"name": "Lumiere",
	"author": "Clarkx",
	"description": "Interactive Lighting add-on for Blender.",
	"version": (0, 4),
	"blender": (2, 91, 0),
	"location": "3D View",
	"warning": "",
	"wiki_url": "",
	"support": 'COMMUNITY',
	"category": "Lighting"
	}


import imp

from . import lumiere_utils
imp.reload(lumiere_utils)
from . import lumiere_draw
imp.reload(lumiere_draw)
from .lights import lumiere_lights
imp.reload(lumiere_lights)
from .lights import lumiere_lights_ui
imp.reload(lumiere_lights_ui)
from .lights import lumiere_lights_gizmo
imp.reload(lumiere_lights_gizmo)
from .lights import lumiere_lights_materials
imp.reload(lumiere_lights_materials)
from . import lumiere_op
imp.reload(lumiere_op)
from . import lumiere_preferences
imp.reload(lumiere_preferences)
from .platform import lumiere_platform
imp.reload(lumiere_platform)
from .platform import lumiere_platform_gizmos
imp.reload(lumiere_platform_gizmos)
from .platform import lumiere_platform_ui
imp.reload(lumiere_platform_ui)
from .platform import lumiere_platform_materials
imp.reload(lumiere_platform_materials)

import bpy
import os
import shutil

presets_folder = bpy.utils.script_paths(subdir="presets")
addons_folder = bpy.utils.script_paths(subdir="addons")
Lumiere_presets = os.path.join(presets_folder[0], 'object', 'Lumiere_presets')

# register
##################################

def register():
	addon = bpy.context.preferences.addons.get("lumiere")
	lumiere_preferences.register()
	lumiere_lights_ui.register()
	lumiere_lights_gizmo.register()
	lumiere_platform_gizmos.register()
	lumiere_platform_ui.register()
	lumiere_op.register()
	print("Registered Lumiere")


def unregister():
	lumiere_op.unregister()
	lumiere_lights_ui.unregister()
	lumiere_lights_gizmo.unregister()
	lumiere_platform_ui.unregister()
	lumiere_platform_gizmos.unregister()
	lumiere_preferences.unregister()
	print("Unregistered Lumiere")


if __name__ == "__main__":
    register()
