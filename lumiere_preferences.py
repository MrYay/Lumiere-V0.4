import bpy
from bpy.props import (
	IntProperty,
	FloatProperty,
	EnumProperty,
	PointerProperty,
	FloatVectorProperty,
	StringProperty,
	BoolProperty,
	)

# -------------------------------------------------------------------- #
## Preferences
class LumiereAddonPreferences(bpy.types.AddonPreferences):
	"""Preferences for Lumiere"""

	bl_idname = __package__

	type_preferences : EnumProperty(
		items=(('lights', "Lights", "", 0),
			   ('platform', "Platform", "", 1),
			   # ('cameras', "Cameras", "", 2),
			   # ('world', "World", "", 3),
			   ('render', "Render", "", 2),
			   ('collections', "Collections", "", 3),
			   ))

#---Use keys during raycast
	modal_keys : BoolProperty(
							   name="Modal keys",
							   description="Activate the keys during modal operation",
							   default=True)

#---Lights 3d gizmos
	lights_3dgizmos : BoolProperty(
							   name="Gizmos lights",
							   description="Activate the gizmos for the lights",
							   default=True)

#---Lights size
	lights_size : FloatProperty(
							   name="Lights size",
							   description="Default light size",
							   default=1)

#---Lights rounding
	lights_rounding : FloatProperty(
							   name="Lights rounding",
							   description="Default light rounding",
							   default=0.25)

#---Lights 2d buttons
	lights_2dgizmos : BoolProperty(
							   name="Buttons lights",
							   description="Activate the 2d buttons in the 3d view",
							   default=True)

#---Platform 3d gizmos
	platform_3dgizmos : BoolProperty(
							   name="Gizmos platform",
							   description="Activate the gizmos for the Platform",
							   default=True)

#---Platform 2d buttons
	platform_2dgizmos : BoolProperty(
							   name="Buttons platform",
							   description="Activate the 2d buttons in the 3d view",
							   default=True)

#---Camera 3d gizmos
	camera_3dgizmos : BoolProperty(
							   name="Gizmos camera",
							   description="Activate the gizmos for the camera",
							   default=True)

#---Camera 2d buttons
	camera_2dgizmos : BoolProperty(
							   name="Buttons camera",
							   description="Activate the 2d buttons in the 3d view",
							   default=True)

#---Activate render pause
	render_pause : BoolProperty(
							   name="Render Pause",
							   description="Pause the render during interactive to save time",
							   default=False)

#---Primary collection name
	primary_collection : StringProperty(
							   name="Primary Collection",
							   description="Default name of the primary collection",
							   default="Lumiere")

#---Lights collection name
	lights_collection : StringProperty(
							   name="Lights Collection",
							   description="Default name of the lights collection",
							   default="Lights")

#---Camera collection name
	camera_collection : StringProperty(
							   name="Camera Collection",
							   description="Default name of the camera collection",
							   default="Camera")

#---Platform collection name
	platform_collection : StringProperty(
							   name="Platform Collection",
							   description="Default name of the platform collection",
							   default="Platform")

#---Camera location
	camera_location : FloatVectorProperty(
							   name="Camera location",
							   description="Default location of the camera",
							   default=(2,0,0.5))

#---Camera Rotation
	camera_rotation : FloatVectorProperty(
							   name="Camera rotation",
							   description="Default rotation of the camera",
							   default=(90,0,90))

	def draw(self, context):
		layout = self.layout
		row= layout.row(align=True)
		row.prop(self, "type_preferences", expand=True)
		row.scale_y = 1.5
		if self.type_preferences == 'lights':
			layout.prop(self, "lights_3dgizmos")
			layout.prop(self, "lights_2dgizmos")
			layout.prop(self, "modal_keys")
			layout.prop(self, "lights_size")
		elif self.type_preferences == 'platform':
			layout.prop(self, "platform_3dgizmos")
			layout.prop(self, "platform_2dgizmos")
		elif self.type_preferences == 'collections':
			layout.prop(self, "primary_collection")
			layout.prop(self, "lights_collection")
			layout.prop(self, "camera_collection")
			layout.prop(self, "platform_collection")
		# elif self.type_preferences == 'camera':
		# 	layout.prop(self, "camera_location")
		# 	layout.prop(self, "camera_rotation")
		elif self.type_preferences == 'render':
			layout.prop(self, "render_pause")

# -------------------------------------------------------------------- #
## Register
classes = [
	LumiereAddonPreferences,
	]

def register():
	from bpy.utils import register_class
	for cls in classes:
		register_class(cls)

def unregister():
	from bpy.utils import unregister_class
	for cls in reversed(classes):
		unregister_class(cls)
