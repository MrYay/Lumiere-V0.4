import bpy

from ..lumiere_utils import (
	get_collection,
	get_preferences,
	)

from mathutils import (
	Vector,
	Matrix,
	Quaternion,
	Euler,
	)

from .lumiere_lights_materials import (
	softbox_mat,
	lamp_mat,
	)

# -------------------------------------------------------------------- #
# Softbox
def create_softbox(softbox_name = "Lumiere"):
	"""Create the panel light with modifiers"""

	primary_col, light_col, platform_col = get_collection()
	addon_prefs = get_preferences()

	# Set Lumiere as the active layer collection
	primary_layer = bpy.context.view_layer.layer_collection.children[primary_col.name]
	bpy.context.view_layer.active_layer_collection = primary_layer.children[light_col.name]

	# Add a primitive plane in the active collection
	bpy.ops.mesh.primitive_plane_add(size=addon_prefs.lights_size, calc_uvs=False, align='VIEW', enter_editmode=False, location=(0.0, 0.0, 0.0), rotation=(0.0, 0.0, 90.0))
	light = bpy.context.view_layer.objects.active
	light.name = softbox_name

	# Select the light and make it active
	bpy.ops.object.select_all(action='DESELECT')
	light.select_set(state=True)
	bpy.context.view_layer.objects.active = bpy.data.objects[light.name]

	# Add UV
	bpy.ops.object.editmode_toggle()
	bpy.ops.uv.smart_project(angle_limit=66, island_margin=0, user_area_weight=0)
	bpy.ops.uv.reset()
	bpy.ops.object.editmode_toggle()

	# Add the material
	softbox_mat(light)

	# Change the visibility
	light.display_type = 'WIRE'
	light.show_transparent = True
	light.show_wire = True
	light.cycles_visibility.camera = False
	light.cycles_visibility.shadow = False

	# Add Bevel
	light.modifiers.new("Bevel", type='BEVEL')

	#2.9
	if float(bpy.app.version_string[:3]) > 2.8 :
		light.modifiers["Bevel"].affect = 'VERTICES'
	else:
		light.modifiers["Bevel"].use_only_vertices = True
	light.modifiers["Bevel"].use_clamp_overlap = True
	light.modifiers["Bevel"].loop_slide = True
	light.modifiers["Bevel"].width = .25
	light.modifiers["Bevel"].segments = 5
	light.modifiers["Bevel"].profile = .5
	light.modifiers["Bevel"].show_expanded = False

	# Set back the active collection to the master collection
	bpy.context.view_layer.active_layer_collection =  bpy.context.view_layer.layer_collection

	return(light)

# -------------------------------------------------------------------- #
# Blender Light
"""Create a blender light"""
def create_lamp(type, name = "Lumiere"):
	primary_col, light_col, platform_col = get_collection()

	# Create the lamp
	light_data = bpy.data.lights.new(name = name, type = type.upper())
	light = bpy.data.objects.new(name = name, object_data = light_data)
	if type == "Area":
		light_data.size = light_data.size_y = 0.5
		light_data.shape = "RECTANGLE"
	else:
		light_data.shadow_soft_size = 0.5

	# Add the light to the collection
	light_col.objects.link(light)

	# Initialize MIS / Type / Name
	light.data.cycles.use_multiple_importance_sampling = True

	# Select and active the light
	bpy.ops.object.select_all(action='DESELECT')
	light.select_set(state=True)
	# light_selected = True
	bpy.context.view_layer.objects.active = light

	# Create nodes
	lamp_mat(light)

	return(light)
