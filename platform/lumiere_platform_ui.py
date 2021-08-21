import bpy
import os
from bpy.types import Panel, Operator, Menu
from bpy.props import (
	IntProperty,
	FloatProperty,
	EnumProperty,
	PointerProperty,
	FloatVectorProperty,
	StringProperty,
	BoolProperty,
	)

import bpy.utils.previews

from .lumiere_platform import(
	update_platform,
	)

from .lumiere_platform_materials import(
	platform_update_mat,
	)

from ..lumiere_utils import (
	get_collection,
	)

# -------------------------------------------------------------------- #
def update_uilist(self,context):
	primary_col, light_col, platform_col = get_collection()
	bpy.ops.object.select_all(action='DESELECT')
	platforms = platform_col.all_objects
	platforms[context.scene.Lumiere_platforms_list_index].select_set(True)
	context.view_layer.objects.active = platforms[context.scene.Lumiere_platforms_list_index]

# -------------------------------------------------------------------- #
def update_shadow_catcher(self, context):
	"""Update the shadow catcher"""
	platform = bpy.data.objects[self.id_data.name]
	platform.cycles.is_shadow_catcher = platform.Lumiere_platform.shadow_catcher
	platform.cycles_visibility.glossy = not platform.Lumiere_platform.shadow_catcher
	bpy.data.scenes[context.scene.name].render.film_transparent = platform.Lumiere_platform.shadow_catcher
# -------------------------------------------------------------------- #
def get_platform_bevel_offset(self):
	"""Get the max bevel offset for the platform"""
	platform = bpy.data.objects[self.id_data.name]
	scale = platform.Lumiere_platform.scale
	scale_x = (platform.Lumiere_platform.scale_x * scale)*2
	scale_y = (platform.Lumiere_platform.scale_y * scale)*2
	try:
		if self['bevel_offset'] < 0:
			self['bevel_offset'] = 0
		elif self['bevel_offset'] > min([scale_x,scale_y]):
			self['bevel_offset'] = min(scale_x,scale_y)

	except KeyError:
		self['bevel_offset'] = 0

	return self['bevel_offset']

def set_platform_bevel_offset(self, value):
	self['bevel_offset'] = value

# -------------------------------------------------------------------- #
## Platform Properties
class Lumiere_platforms_prop(bpy.types.PropertyGroup):

#---List of platforms
	platform_type : EnumProperty(name="Platform type:",
								description="List of lights sources:\n"+
								"\u2022 L Curve : Platform with the shape of a ""L""\n"+
								"\u2022 S Curve : Platform with the shape of a ""S""\n"+
								"\u2022 C Curve : Platform with the shape of a ""C""\n"+
								"\u2022 3 Walls : Platform with 3 walls around it\n"+
								"\u2022 Corner : Platform with the shape of a corner\n"+
								"\u2022 Box : Platform with the shape of a box\n"+
								"Selected",
								items =(
								("L_curve", "L curve", "", 0),
								("S_curve", "S curve", "", 1),
								("C_curve", "C curve", "", 2),
								("3_walls", "3 walls", "", 3),
								("Corner", "Corner", "", 4),
								("Box", "Box", "", 5),
								),
								default=None,
								update=update_platform,
								)

#---Height
	height : FloatProperty(
						  name="Height",
						  description="Height",
						  min=0, max=100000,
						  soft_min=0, soft_max=50.0,
						  default=0,
						  precision=2,
						  unit='LENGTH',
						  update=update_platform,
						  )

#---Lock scale on x and y
	lock_scale : BoolProperty(name = "Lock scale on x and y",
						description = "Lock scale on x and y",
						default=True,
						update=update_platform,
						)

#---Scale
	scale : FloatProperty(
						  name="Scale",
						  description="Scale",
						  min=0.001, max=100000,
						  soft_min=0.001, soft_max=50.0,
						  default=1,
						  precision=2,
						  unit='LENGTH',
						  update=update_platform,
						  )

#---Scale x
	scale_x : FloatProperty(
						  name="Scale x",
						  description="Scale x",
						  min=0.001, max=100000,
						  soft_min=0.001, soft_max=50.0,
						  default=0.5,
						  precision=2,
						  unit='LENGTH',
						  update=update_platform,
						  )

#---Scale y
	scale_y : FloatProperty(
						  name="Scale y",
						  description="Scale y",
						  min=0.001, max=100000,
						  soft_min=0.001, soft_max=50.0,
						  default=0.5,
						  precision=2,
						  unit='LENGTH',
						  update=update_platform,
						  )

#---Ceiling
	ceiling : FloatProperty(
						  name="Ceiling",
						  description="Ceiling",
						  min=0.001, max=100000,
						  soft_min=0.001, soft_max=50.0,
						  default=0.5,
						  precision=2,
						  unit='LENGTH',
						  update=update_platform,
						  )

#---Shade smooth
	shade_smooth : BoolProperty(
						name="Shade smooth",
						description="Shade smooth.",
						default=True,
						update=update_platform
						)

#---Bevel offset
	bevel_offset : FloatProperty(
						  name="Bevel offset",
						  description="Bevel offset",
						  min=0, max=10000,
						  soft_min=0, soft_max=10000,
						  default=0,
						  precision=2,
						  step=.08,
						  unit='LENGTH',
						  get=get_platform_bevel_offset,
						  set=set_platform_bevel_offset,
						  update=update_platform,
						  )

#---Bevel segment
	bevel_segment : FloatProperty(
						  name="Bevel segments",
						  description="Bevel segments",
						  min=1, max=1000,
						  soft_min=1, soft_max=50,
						  default=3,
						  precision=0,
						  step=5,
						  update=update_platform,
						  )

#---Bevel profil
	bevel_profil : FloatProperty(
						  name="Bevel profil",
						  description="Bevel profil",
						  min=0, max=1,
						  default=0.5,
						  precision=6,
						  step=.1,
						  update=update_platform,
						  )

#---Platform location on local axis
	location : FloatVectorProperty(
							name="Location",
							description="Platform location on local axis",
							)

#---Shadow catcher
	shadow_catcher : BoolProperty(
						name="Shadow catcher",
						description="Only render shadow",
						default=False,
						update=update_shadow_catcher
						)

# -------------------------------------------------------------------- #
## Materials

#---Color type
	color_type : EnumProperty(name="Color type",
						  description="Use a simple colr or a gradient from front to back.\n"+\
						  "\u2022 Color : Color of the platform.\n"+\
						  "\u2022 Gradient : Linear gradient from front to back.\n"+\
						  "Selected",
						  items = (
						  ("Color", "Color", "", 0),
						  ("Gradient", "Gradient", "", 1),
						  ),
						  default=None,
						  )

#---Base Color of the platform
	platform_color : FloatVectorProperty(
									 name = "Color",
									 description="Base Color of the platform",
									 subtype = "COLOR",
									 size = 4,
									 min = 0.0,
									 max = 1.0,
									 default = (0.2,0.2,0.2,1.0),
									 update=platform_update_mat,
									 )

#---Specular value
	specular_value : FloatProperty(
							name="Specular value",
							description="Amount of specular",
							min=0, max=100,
							soft_min=0, soft_max=1,
							default=1,
							update=platform_update_mat,
							)

#---Specular range
	specular_range : FloatProperty(
							name="Specular range",
							description="Range of specular",
							min=0, max=1,
							default=0,
							update=platform_update_mat,
							)

#---Roughness value
	roughness_value : FloatProperty(
							name="Roughness value",
							description="Amount of roughness",
							min=0, max=100,
							soft_min=0, soft_max=1,
							default=1,
							update=platform_update_mat,
							)

#---Translucency
	translucency : FloatProperty(
							name="Translucency",
							description="Amount of translucency",
							min=0, max=1,
							precision=2,
							update=platform_update_mat,
							)

# -------------------------------------------------------------------- #
class PLATFORMS_UL_list(bpy.types.UIList):
	def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
		object = data
		row = layout.row(align=True)
		sub=row.row(align=True)
		sub.scale_x = 0.65
		sub.label(text="%d" % (index))

		sub=row.row(align=True)
		sub.scale_x = 0.25
		sub.prop(item.Lumiere_platform,"platform_color",text='')

		sub=row.row(align=True)
		sub.scale_x = 1.75
		sub.prop(item,"name",text='')

		sub=row.row(align=True)
		sub.prop(item,"hide_viewport",text='')

		sub=row.row(align=True)
		sub.prop(item,"hide_render",text='')

# -------------------------------------------------------------------- #
## Parent panel
class POLLPLATFORM_PT_Lumiere:
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"

	@classmethod
	def poll(cls, context):
		primary_col, light_col, platform_col = get_collection()

		if primary_col:
			if (len(context.selected_objects)>0):
				if platform_col and len(platform_col.objects) > 0 :
					return context.view_layer.objects.active.name in platform_col.all_objects
			else:
				return False
		return False

# -------------------------------------------------------------------- #
class MAINPLATFORM_PT_Lumiere(Panel):
	bl_idname = "MAINPLATFORM_PT_Lumiere"
	bl_label = "Platform:"
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = "Lumiere"
	bl_context = "objectmode"

	def platform_in_scene(self, context):
		primary_col, light_col, platform_col = get_collection()
		if platform_col and (len(context.selected_objects)>0) and \
		len(platform_col.objects) > 0 and \
		context.active_object.name in platform_col.objects:
			return True
		else:
			return False

	@classmethod
	def poll(cls, context):
		primary_col, light_col, platform_col = get_collection()

		if primary_col:
			if platform_col and ((len(context.selected_objects)==0) or context.view_layer.objects.active.name not in platform_col.all_objects):
				return context.scene.Lumiere.create_menu=="Platform"
			else:
				return context.view_layer.objects.active.name in platform_col.all_objects
		else:
			return context.scene.Lumiere.create_menu=="Platform"

	def draw_header_preset(self, context):
		scene = context.scene
		layout = self.layout
		col = layout.column(align=False)
		row = col.row(align=True)
		row.prop(scene.Lumiere, "create_menu", text="", expand=True)

	def draw(self, context):
		primary_col, light_col, platform_col = get_collection()
		platform = context.active_object
		scene = context.scene
		layout = self.layout
		layout.use_property_split = True # Active single-column layout
		layout.use_property_decorate = False  # No animation.
		flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=True)
		col = flow.column(align=False)
		col.ui_units_x = 7
		if self.platform_in_scene(context):
			col.prop(platform.Lumiere_platform, "platform_type")
		else:
			col.operator("lumiere.platform_operator", text="Add platform")
			col.template_list("PLATFORMS_UL_list", "", platform_col, "all_objects", context.scene, "Lumiere_platforms_list_index", rows=2)
# -------------------------------------------------------------------- #
class PLATFORM_PT_Lumiere_options(POLLPLATFORM_PT_Lumiere, Panel):
	bl_idname = "PLATFORM_PT_Lumiere_options"
	bl_label = "Options:"
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = "Lumiere"
	bl_context = "objectmode"

	def draw(self, context):
		platform = context.active_object
		scene = context.scene
		layout = self.layout
		layout.use_property_split = True # Active single-column layout
		layout.use_property_decorate = False  # No animation.
		flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=True)
		col = flow.column(align=False)
		col.ui_units_x = 7

		if platform.Lumiere_platform.lock_scale:
			row = col.row(align=True)
			row.prop(platform.Lumiere_platform, "scale", text="Scale")
			row.prop(platform.Lumiere_platform, "lock_scale", text="", emboss=False, icon='DECORATE_LOCKED')

		if not platform.Lumiere_platform.lock_scale:
			row = col.row(align=True)
			row.prop(platform.Lumiere_platform, "scale_x")
			row.prop(platform.Lumiere_platform, "lock_scale", text="", emboss=False, icon='DECORATE_UNLOCKED')
			row = col.row(align=True)
			row.prop(platform.Lumiere_platform, "scale_y")
			row.prop(platform.Lumiere_platform, "lock_scale", text="", emboss=False, icon='DECORATE_UNLOCKED')

		col = flow.column(align=False)
		col.prop(platform.Lumiere_platform, "height")

		if platform.Lumiere_platform.platform_type == "C_curve":
			col.prop(platform.Lumiere_platform, "ceiling")

		col.prop(platform.Lumiere_platform, "bevel_offset")
		col.prop(platform.Lumiere_platform, "bevel_segment")
		col.prop(platform.Lumiere_platform, "bevel_profil", slider=True)
		flow = col.column_flow()
		flow.prop(platform.Lumiere_platform, "shade_smooth", text="Shade smooth")
		flow.prop(platform.Lumiere_platform, "shadow_catcher", text="Shadow catcher")


# -------------------------------------------------------------------- #
class PLATFORM_PT_Lumiere_materials(POLLPLATFORM_PT_Lumiere, Panel):
	bl_idname = "PLATFORM_PT_Lumiere_materials"
	bl_label = "Materials:"
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = "Lumiere"
	bl_context = "objectmode"

	def draw(self, context):
		platform = context.active_object
		scene = context.scene
		layout = self.layout
		layout.use_property_split = True # Active single-column layout
		layout.use_property_decorate = False  # No animation.
		flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=True)
		col = flow.column(align=True)
		col.ui_units_x = 7

		col.prop(platform.Lumiere_platform, 'platform_color')
		col.separator()
		col.prop(platform.Lumiere_platform, 'specular_value', text="Specular")
		col.prop(platform.Lumiere_platform, 'specular_range', text="Range")
		col.separator()
		col.prop(platform.Lumiere_platform, 'roughness_value', text="Roughness")
		col.separator()
		col.prop(platform.Lumiere_platform, 'translucency')

# -------------------------------------------------------------------- #
## Register
classes = [
	MAINPLATFORM_PT_Lumiere,
	PLATFORM_PT_Lumiere_options,
	PLATFORM_PT_Lumiere_materials,
	Lumiere_platforms_prop,
	PLATFORMS_UL_list,
	]

def register():
	from bpy.utils import register_class
	for cls in classes:
		register_class(cls)
	bpy.types.Object.Lumiere_platform = bpy.props.PointerProperty(type=Lumiere_platforms_prop)
	bpy.types.Scene.Lumiere_platforms_list_index = bpy.props.IntProperty(name = "Index", default = 0, update=update_uilist)

def unregister():
	from bpy.utils import unregister_class
	for cls in reversed(classes):
		unregister_class(cls)
	del bpy.types.Object.Lumiere_platform
	del bpy.types.Scene.Lumiere_platforms_list_index
