import bpy
import bmesh
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

from mathutils import (
	Vector,
	)

from .lumiere_lights import (
	create_lamp,
	create_softbox,
	)

from .lumiere_lights_materials import (
	update_mat,
	softbox_mat,
	lamp_mat,
	update_lamp,
	)

from ..lumiere_utils import (
	get_mat_name,
	get_collection,
	get_preferences,
	update_spherical_coordinate,
	)
# -------------------------------------------------------------------- #
def update_type_light(self, context):
	"""Change the selected light to a new one"""
	light = bpy.data.objects[self.id_data.name]

	values = {}
	lumiere_dict = {}
	lumiere_dict[light.name] = light['Lumiere'].to_dict()
	lumiere_dict[light.name]['location'] = light.location.copy()
	lumiere_dict[light.name]['rotation'] = light.rotation_euler.copy()
	lumiere_dict[light.name]['rotation2'] = light.Lumiere.rotation
	lumiere_dict[light.name]['hit'] = Vector(light.Lumiere.hit).copy()
	lumiere_dict[light.name]['direction'] = Vector(light.Lumiere.direction).copy()
	lumiere_dict[light.name]['reflect'] = light.Lumiere.reflect_angle
	lumiere_dict[light.name]['parent'] = light.parent

	def get_light_values():
		light['Lumiere'] = lumiere_dict[values['old_name']]
		light.parent = lumiere_dict[values['old_name']]["parent"]
		light.matrix_parent_inverse = lumiere_dict[values['old_name']]["parent"].matrix_world.inverted()
		light.location = lumiere_dict[values['old_name']]["location"]
		light.rotation_euler = lumiere_dict[values['old_name']]["rotation"]
		light.Lumiere.rotation = lumiere_dict[values['old_name']]["rotation2"]
		light.Lumiere.hit = lumiere_dict[values['old_name']]["hit"]
		light.Lumiere.direction = lumiere_dict[values['old_name']]["direction"]
		light.Lumiere.reflect_angle = lumiere_dict[values['old_name']]["reflect"]
		light.Lumiere.scale_x = light.Lumiere.scale_x

	# Save values for the new light
	values['old_name'] = light.name
	values['old_type'] = light.Lumiere.light_type.upper()

#-- The light is a lamp to be replaced by a mesh
	if light.type == "LIGHT":
		if light.Lumiere.light_type == "Softbox":
			lamp = bpy.data.lights[light.data.name]
			bpy.data.lights.remove(lamp, do_unlink=True, do_id_user=True, do_ui_user=True)
			if values['old_name'] in bpy.data.objects:
				for ob in  bpy.data.objects:
					if ob.data.name == values['old_name']:
						light = ob
			else:
				light = create_softbox(values['old_name'])
				light.data.name = values['old_name']
				get_light_values()
				update_mat(self, context)
		else:
			if values['old_type'] != context.object.data.type:
				context.object.data.type = values['old_type']
				light.Lumiere.scale_x = light.Lumiere.scale_x
				update_lamp(light)

#-- The light is a mesh to be replaced by a lamp
	elif light.type == "MESH" and light.Lumiere.light_type != "Softbox":
		new_type = light.Lumiere.light_type

		# Delete the old mesh from the collection
		mesh = bpy.data.meshes[light.data.name]

		# Create a new light
		light = create_lamp(type = new_type, name = values['old_name'])
		get_light_values()
		update_lamp(light)

		bpy.data.meshes.remove(mesh, do_unlink=True, do_id_user=True, do_ui_user=True)

	del lumiere_dict[values['old_name']]

# -------------------------------------------------------------------- #
def update_softbox_rounding(self, context):
	"""Update the rounding value of the softbox"""
	light = bpy.data.objects[self.id_data.name]
	light.modifiers["Bevel"].width = light.Lumiere.softbox_rounding

# -------------------------------------------------------------------- #
def update_texture_scale(self, context):
	"""Update the texture scale"""
	light = bpy.data.objects[self.id_data.name]

	if light.type == 'MESH':
		me = light.data
		bm = bmesh.new()
		bm.from_mesh(me)

		uv_layer = bm.loops.layers.uv.active

		if light.Lumiere.lock_scale:
			scale_x = scale_y = light.Lumiere.img_scale / 2 + .5
		else:
			scale_x = (light.Lumiere.img_scale * light.Lumiere.scale_x) / 2 + .5
			scale_y = (light.Lumiere.img_scale * light.Lumiere.scale_y) / 2 + .5

		for f in bm.faces:
			f.loops[3][uv_layer].uv = (scale_x, scale_y)
			f.loops[2][uv_layer].uv = (1-scale_x, scale_y)
			f.loops[1][uv_layer].uv = (1-scale_x, 1-scale_y)
			f.loops[0][uv_layer].uv = (scale_x, 1-scale_y)
		bm.to_mesh(me)
	else:
		update_lamp(light)

# -------------------------------------------------------------------- #
def get_spin(self):
	"""Rotate the light on the Z axis"""
	light = bpy.data.objects[self.id_data.name]
	return light.rotation_euler.to_matrix().to_euler('ZYX').z

def set_spin(self, spin):
	# https://blender.stackexchange.com/questions/118057/rotate-object-on-local-axis-using-a-slider
	light = bpy.context.object
	rot = light.rotation_euler.to_matrix().to_euler('ZYX')
	rot.z = spin
	light.rotation_euler = rot.to_matrix().to_euler(light.rotation_mode)

# -------------------------------------------------------------------- #
def get_rotation(self):
	"""Rotate the light on the Z axis"""
	light = bpy.data.objects[self.id_data.name]
	try:
		rotation = self["rotation"]
		if rotation < -359.9:
			self["rotation"] = 720 + rotation
		elif rotation > 359.9:
			self["rotation"] = -720 + rotation

		return rotation
	except KeyError:
		self["rotation"] = 0
		return self["rotation"]

def set_rotation(self, value):
	self['rotation'] = value

# -------------------------------------------------------------------- #
def get_tilt(self):
	"""Incline the light """
	light = bpy.data.objects[self.id_data.name]
	try:
		rotation = self["tilt"]
		if rotation < -179.9:
			self["tilt"] = 360 + rotation
		elif rotation > 179.9:
			self["tilt"] = -360 + rotation

		return rotation
	except KeyError:
		self["tilt"] = 0
		return self["tilt"]

def set_tilt(self, value):
	self['tilt'] = value


# -------------------------------------------------------------------- #
def update_uilist(self,context):
	primary_col, light_col, platform_col = get_collection()
	bpy.ops.object.select_all(action='DESELECT')
	lights = light_col.all_objects
	lights[context.scene.Lumiere_lights_list_index].select_set(True)
	context.view_layer.objects.active = lights[context.scene.Lumiere_lights_list_index]

# -------------------------------------------------------------------- #
def update_rotation_tilt(self,context):
	"""Update the location and rotation of the light around the targeted object"""
	light = bpy.data.objects[self.id_data.name]

	update_spherical_coordinate(self,context,light=bpy.data.objects[self.id_data.name])

	# Update the shadow location
	if context.scene.is_running == False:
		depsgraph = context.evaluated_depsgraph_get()
		if light.parent : light.parent.hide_viewport = True
		result, hit_location, _, _, _, _ = context.scene.ray_cast(depsgraph, Vector(light.Lumiere.hit), (Vector(light.Lumiere.hit) - light.location))

		if result:
			light.Lumiere.shadow = hit_location
		else:
			light.Lumiere.shadow = (0,0,0)
		if light.parent : light.parent.hide_viewport = False

# -------------------------------------------------------------------- #
def update_ratio(self,context):
	"""Update the ratio scale/energy"""
	light = context.object
	if light.Lumiere.ratio:
		if light.type == 'MESH':
			light.Lumiere.save_energy = (light.scale[0] * light.scale[1]) * light.Lumiere.energy

# -------------------------------------------------------------------- #
def update_lock_scale(self,context):
	"""Update the scale xy of the light"""
	update_texture_scale(self, context)

# -------------------------------------------------------------------- #
def update_scale(self,context):
	"""Update the x dimension of the light"""
	light = bpy.data.objects[self.id_data.name]
	scale_x = light.Lumiere.scale_x * light.Lumiere.scale_xy
	scale_y = light.Lumiere.scale_y * light.Lumiere.scale_xy

	if light.type == 'MESH':
		light.scale[0] = scale_x*2
		light.scale[1] = scale_y*2
		update_texture_scale(self, context)
		if light.Lumiere.ratio:
			light.Lumiere.energy = light.Lumiere.save_energy / (light.scale[0] * light.scale[1])

	else:
		if light.data.type == "AREA":
			if light.data.shape not in ('SQUARE', 'DISK'):
				light.scale[0] = light.scale[1] = 1
				light.data.size = scale_x*2
				light.data.size_y = scale_y*2
			else:
				light.scale[0] = light.scale[1] = 1
				light.data.size = light.data.size_y = scale_y*2
		elif light.data.type == "SUN":
			light.data.angle = scale_y
		else:
			light.data.shadow_soft_size = scale_y

	if light.scale[0] < 0.001:
		light.scale[0] = 0.001
	if light.scale[1] < 0.001:
		light.scale[1] = 0.001

# -------------------------------------------------------------------- #
def target_poll(self, object):
	"""Target only this object"""
	primary_col, light_col, platform_col = get_collection()

	if object.name not in light_col.all_objects:
		return object

# -------------------------------------------------------------------- #
def update_select_only(self, context):
	"""Show only this light and hide all the other"""
	light = bpy.data.objects[self.id_data.name]
	primary_col, light_col, platform_col = get_collection()

	# Active only the visible light
	context.view_layer.objects.active = light

	# Deselect and hide all the lights in the scene and show the active light
	bpy.ops.object.select_all(action='DESELECT')
	for ob in light_col.objects:
		if ob.name != light.name:
			if light.Lumiere.select_only:
				ob.hide_viewport = True
			else:
				ob.hide_viewport = False

	# Select only the visible light
	light.select_set(True)

# -------------------------------------------------------------------- #
def update_range(self,context):
	"""Update the distance of the light from the object target"""
	light = bpy.data.objects[self.id_data.name]

	mat = get_mat_name(light)
	light.location = Vector(light.Lumiere.hit) + (Vector(light.Lumiere.direction) * light.Lumiere.range)
	track  = light.location - Vector(light.Lumiere.hit)
	rotaxis = (track.to_track_quat('Z','Y'))
	light.rotation_euler = rotaxis.to_euler()

#----------------------------------------------- #
## Items
def items_light_type(self, context):
	"""Define the different items for the lights"""

	items = {
		("Area", "Area", "", "LIGHT_AREA", 0),
		("Point", "Point", "", "LIGHT_POINT", 1),
		("Sun", "Sun", "", "LIGHT_SUN", 2),
		("Spot", "Spot", "", "LIGHT_SPOT", 3),
		("Softbox", "Softbox", "", "MESH_PLANE", 4),
		}

	return items

def items_color_type(self, context):
	"""Define the different items for the color choice of lights"""

	if bpy.data.objects[self.id_data.name].type == "MESH":
		items = {
				("Color", "Color", "", 0),
				("Linear", "Linear", "", 1),
				("Blackbody", "Blackbody", "", 2),
				("Spherical", "Spherical", "", 3),
				("Reflector", "Reflector", "", 4),
				}
	else:
		if bpy.data.objects[self.id_data.name].Lumiere.light_type == "Sun":
			items = {
					("Color", "Color", "", 0),
					("Blackbody", "Blackbody", "", 1),
					}
		else:
			items = {
					("Color", "Color", "", 0),
					("Blackbody", "Blackbody", "", 1),
					("Gradient", "Gradient", "", 2),
					}

	return items

def items_material_menu(self, context):
	""" Define the different items materials """

	if bpy.context.scene.render.engine == 'CYCLES' or context.view_layer.objects.active.type == 'MESH' :
			items = {
					("Color", "Color", "Color", "COLOR", 0),
					("Texture", "Texture", "Texture", "FILE_IMAGE", 1),
					("IES", "IES", "IES","OUTLINER_OB_LIGHT", 2),
					("Options", "Options", "Options","PREFERENCES", 3),
					}
	else:
			items = {
					("Color", "Color", "Color", "COLOR", 0),
					("Options", "Options", "Options","PREFERENCES", 1),
					}

	return items

# -------------------------------------------------------------------- #
def get_main(self):
	"""Update main menu in panel"""
	primary_col, light_col, platform_col = get_collection()
	try:
		if primary_col is not None:
			if (len(bpy.context.selected_objects)>0):
				obj = bpy.context.view_layer.objects.active
				if obj.name in primary_col.all_objects:
					if light_col and obj.name in light_col.all_objects:
						self['create_menu'] = 0
					elif platform_col and obj.name in platform_col.all_objects:
						self['create_menu'] = 1
		return self['create_menu']
	except KeyError or AttributeError:
		self['create_menu'] = 0
		return 0

def set_main(self, value):
	bpy.ops.object.select_all(action='DESELECT')
	self['create_menu'] = value

# -------------------------------------------------------------------- #
#---Main menu options
class Lumiere_main_prop(bpy.types.PropertyGroup):

	create_menu : EnumProperty(
				name="Main menu",
				description="Lighting options:\n"+
				"\u2022 Light: Light options\n"+
				"\u2022 Platform: Platform options\n"+
				"Selected",
				items = {
				("Light", "Light", "Light", "LIGHT", 0),
				("Platform", "Platform", "Platform","OUTLINER_OB_SURFACE", 1),
				},
				get=get_main,
				set=set_main,
				default= None,
				)

#---List of lights
	light_type : EnumProperty(name="Light type:",
								description="List of lights sources:\n"+
								"\u2022 Panel : Panel object with an emission shader\n"+
								"\u2022 Point : Emit light equally in all directions\n"+
								"\u2022 Sun : Emit light in a given direction\n"+
								"\u2022 Spot : Emit light in a cone direction\n"+
								"\u2022 Area : Emit light from a square or rectangular area\n"+
								"\u2022 Import : Import your previous saved Light / Group lights\n"+
								"Selected",
								items = items_light_type,
								default= None,
								)

# -------------------------------------------------------------------- #
## Light Properties
class Lumiere_lights_prop(bpy.types.PropertyGroup):

#---Strength of the light
	energy : FloatProperty(
						   name="Energy",
						   description="Energy of the light",
						   min=-900000000000.0, max=900000000000.0,
						   soft_min=0.001, soft_max=500.0,
						   default=10,
						   step=20000,
						   precision=2,
						   unit='POWER',
						   update=update_mat
						   )

#---Rotate the light around Z
	rotation : FloatProperty(
						  name="Rotation",
						  description="Rotate the light horizontally around the target",
						  min=-360,
						  max=360,
						  step=20,
						  get=get_rotation,
						  set=set_rotation,
						  update=update_rotation_tilt,
						  )

#---Rotate the light horizontally
	spin : FloatProperty(
						  name="Spin",
						  description="Rotate the light along it's Z axis",
						  step=20,
						  unit='ROTATION',
						  get=get_spin,
						  set=set_spin,
						  )

#---Rotate the light vertically
	tilt : FloatProperty(
						  name="Tilt",
						  description="Incline the light vertically from the target",
						  min=0.0,
						  max=180,
						  step=20,
						  get=get_tilt,
						  set=set_tilt,
						  update=update_rotation_tilt,
						  )

#---Scale the light
	scale_xy : FloatProperty(
						  name="Scale",
						  description="Scale the light",
						  min=0.0001, max=100000,
						  soft_min=0.01, soft_max=100.0,
						  unit='LENGTH',
						  default=0.5,
						  precision=2,
						  update=update_scale,
						  )

#---Scale the light on x
	scale_x : FloatProperty(
						  name="Scale x",
						  description="Scale the light on x",
						  min=0.0001, max=100000,
						  soft_min=0.001, soft_max=100.0,
						  unit='LENGTH',
						  subtype='DISTANCE',
						  step=1,
						  default=.5,
						  precision=2,
						  update=update_scale,
						  )

#---Scale the light on y
	scale_y : FloatProperty(
						  name="Scale y",
						  description="Scale the light on y",
						  min=0.0001, max=100000,
						  soft_min=0.001, soft_max=100.0,
						  unit='LENGTH',
						  subtype='DISTANCE',
						  step=1,
						  default=.5,
						  precision=2,
						  update=update_scale,
						  )

#---Range of the light from the targeted object
	range : FloatProperty(
						  name="Range",
						  description="Distance from the object",
						  min=0.001, max=100000,
						  soft_min=0.01, soft_max=50.0,
						  default=2,
						  precision=2,
						  unit='LENGTH',
						  update=update_range,
						  )

#---Compute the reflection angle from the normal of the target or from the view of the screen.
	reflect_angle : EnumProperty(name="Reflection",
						  description="Compute the light position from the angle view or the normal of the object.\n"+\
						  "\u2022 Accurate : The light will be positioned in order for its reflection to be under the cursor.\n"+\
						  "\u2022 Normal : The light will be positioned in perpendicular to the normal of the face of the targeted object.\n"+\
						  "\u2022 Estimated : The light will be positioned always facing the center of the bounding box.\n"+\
						  "Selected",
						  items = (
						  ("Normal", "Normal", "", 0),
						  ("Estimated", "Estimated", "", 1),
						  ("Accurate", "Accurate", "", 2),
						  ),
						  default=None,
						  )

#---Compute the bounding box center from one object or from a collection of objects.
	estimated_type : EnumProperty(name="Estimated type",
						  description="Compute the bounding box center from one object or from a collection of objects.\n"+\
						  "\u2022 Object : The center will be compute from the targeted object.\n"+\
						  "\u2022 Collection : The center will be compute from all the objects in the same collection the targeted object is from.\n"+\
						  "Selected",
						  items = (
						  ("Object", "Object", "", 0),
						  ("Collection", "Collection", "", 1),
						  ),
						  default=None,
						  )

#---List of lights to change the selected one to
	light_type : EnumProperty(name="Light type:",
								description="List of lights sources:\n"+
								"\u2022 Panel : Panel object with an emission shader\n"+
								"\u2022 Point : Emit light equally in all directions\n"+
								"\u2022 Sun : Emit light in a given direction\n"+
								"\u2022 Spot : Emit light in a cone direction\n"+
								"\u2022 Area : Emit light from a square or rectangular area\n"+
								"\u2022 Import : Import your previous saved Light / Group lights\n"+
								"Selected",
								items=items_light_type,
								# default= None,
								update = update_type_light
								)


#---Define how light intensity decreases over distance
	falloff_type : EnumProperty(name="Falloff",
							  description="Define how light intensity decreases over distance.\n"+
							  "Quadratic: Representation of how light attenuates in the real world.\n"+
							  "Linear   : Distance to the light have a slower decrease in intensity.\n"+
							  "Constant : Useful for distant light sources like the sun or sky.\n"+
							  "Selected",
							  items=(
							  ("0", "Quadratic falloff", "", 0),
							  ("1", "Linear falloff", "", 1),
							  ("2", "Constant falloff", "", 2),
							  ),
							  default='0',
							  update=update_mat)

#---Strength of the falloff
	falloff_strength : FloatProperty(
						  name="Falloff Strength",
						  description="Strength of the falloff",
						  min=0.0, max=1,
						  soft_min=0, soft_max=1,
						  default=0,
						  precision=2,
						  update=update_mat,
						  )

#---Object the light will always target
	target : PointerProperty(type=bpy.types.Object,
							   name="Target",
							   description="Object the light will always target.",
							   poll=target_poll,
							   )

#---BoundingBox center of the targeted object
	bbox_center : FloatVectorProperty(
							   name="bbox_center",
							   description="BoundingBox center of the targeted object.",
							   )

#---List of modes the light can be linked to
	light_mode : EnumProperty(name="Light mode",
								items = {
										("Sky", "Sky", "Sky", 0),
										("Texture", "Texture", "Texture", 1),
										("None", "None", "None", 2),
										},
								default = "None",
								)
# -------------------------------------------------------------------- #
## Materials

#---Base Color of the light
	light_color : FloatVectorProperty(
									 name = "Color",
									 description="Base Color of the light",
									 subtype = "COLOR",
									 size = 4,
									 min = 0.0,
									 max = 1.0,
									 default = (0.8,0.8,0.8,1.0),
									 update=update_mat
									 )

#---Temperature of the light
	blackbody : FloatProperty(
								 name = "Blackbody",
								 description="Temperature of the light",
								 precision=1,
								 update=update_mat,
								 )

#---List of color options
	color_type : EnumProperty(name="Colors",
								description="Colors options:\n"+
								"\u2022 Gradient: Gradient color emission\n"+
								"\u2022 Color: Single color emission\n"+
								"\u2022 Reflector: No emission\n"+
								"\u2022 Blackbody: Spectrum of light emitted by any heated object\n"+
								"Selected",
								items=items_color_type,
								update=update_mat,
								)

#---List of color options
	material_menu : EnumProperty(name="Material",
								description="Material options:\n"+
								"\u2022 Color / Gradient: Base Color of the light\n"+
								"\u2022 Texture: Image texture emission\n"+
								"\u2022 IES: Real world lights intensity distribution\n"+
								"\u2022 Options: Define how light intensity decreases over distance and multiple important sample\n"+
								"Selected",
								items = items_material_menu,
								default=None,
								)

#---Name of image texture
	ies_name : StringProperty(
							  name="Name of the image texture",
							  update=update_mat)

#---Name of image texture
	img_name : StringProperty(
							  name="Name of the image texture",
							  update=update_mat)

#---Texture used for lighting or reflecton only.
	img_reflect_only : BoolProperty(
							 name="Reflection only",
							 description="Use the texture only in the reflection or for the light.",
							 default=True,
							 update=update_mat)

#---Rotate the texture on 90°
	rotate_ninety : BoolProperty(default=False,
								description="Rotate the texture on 90°",
								update=update_mat)

#---Lock image scale on x and y
	img_lock_scale : BoolProperty(name = "Lock",
						description = "Lock image scale on x and y",
						default=True,
						)

#---Scale image texture.
	img_scale : FloatProperty(
							  name="Scale image texture",
							  description="Scale the image texture.",
							  min=0, max=999.0,
							  default=1,
							  precision=2,
							  subtype='NONE',
							  unit='NONE',
							  update=update_texture_scale)

#---Scale IES.
	ies_scale : FloatProperty(
							  name="Scale IES",
							  description="Scale the IES.",
							  min=0,
							  default=1,
							  precision=2,
							  subtype='NONE',
							  unit='NONE',
							  update=update_mat)

#---IES used for lighting or reflecton only.
	ies_reflect_only : BoolProperty(
							 name="Reflection only",
							 description="Use the IES only in the reflection or for the light.",
							 default=True,
							 update=update_mat)

#---Invert the color of the image.
	img_invert : FloatProperty(
							  name="Invert",
							  description="Inverts the colors in the input image, producing a negative.",
							  min=0, max=1.0,
							  default=0,
							  precision=2,
							  subtype='NONE',
							  unit='NONE',
							  update=update_mat)
# -------------------------------------------------------------------- #
## Parameters

#---rounding of the softbox. 1 = round
	softbox_rounding : FloatProperty(
								name="Round",
								description="rounding of the softbox.\n0 = Square\n1 = Round",
								min=0, max=1.0,
								precision=2,
								subtype='NONE',
								unit='NONE',
								update=update_softbox_rounding,
								default=0.25,
								)

#---Vector hit point on target object
	hit : FloatVectorProperty(
							name="Hit",
							description="Vector hit point on target object",
							)

#---Invert the direction of the ray_cast to find the back of the object
	invert_ray_cast : BoolProperty(default=False,
								description="Invert the position so the light will be positioned in the back of the targeted object",
								)

#---Vector direction toward targeted object
	direction : FloatVectorProperty(
							name="Direction",
							description="Vector direction toward targeted object",
							)

#---Vector of the shadow
	shadow : FloatVectorProperty(
							name="Shadow",
							description="Vector of the shadow",
							)

#---Used for ratio between scale and energy
	save_energy : FloatProperty(
						   name="Save energy",
						   )

#---Enable / Disable the ratio between scale/energy
	ratio : BoolProperty(name = "Ratio",
						description = "Enable / Disable the ratio between scale/energy",
						default=False,
						update=update_ratio,
						)

#---Lock scale on x and y
	lock_scale : BoolProperty(name = "Lock scale on x and y",
						description = "Lock scale on x and y",
						default=True,
						# update=update_lock_scale,
						)

#---Enable / Disable the manual position of bbox center
	auto_bbox_center : BoolProperty(name = "Bbox center",
						description = "Enable / Disable the manual position of bbox center",
						default=True)

#---Enable / Disable the gizmos
	gizmo : BoolProperty(name = "Gizmo",
						description = "Enable / Disable the gizmos",
						default=False)

#---Show only this light and hide all the others.
	select_only : BoolProperty(name="Select Only",
							   description="Show only this light and hide all the others",
							   default=False,
							   update=update_select_only)

#---Lock/Unlock the light to the environment
	lock_img : BoolProperty(name="Lock/Unlock the light to the environment",
							)

# -------------------------------------------------------------------- #
class Lumiere_group_prop(bpy.types.PropertyGroup):
	num : StringProperty(
						name="Number",
						description="Number of lights (useful for group)",
						)
	name : StringProperty(
						name="Name",
						description="Name of the light or group",
						)

# -------------------------------------------------------------------- #
# Create custom property group
class Lumiere_ui_lights_Prop(bpy.types.PropertyGroup):
	'''name = StringProperty() '''
	label : bpy.props.StringProperty()
	color : bpy.props.FloatVectorProperty(name = "", subtype = "COLOR", size = 4, default = (0.8,0.8,0.8,1.0))
	# id = IntProperty()

# -------------------------------------------------------------------- #
class LIGHTS_UL_list(bpy.types.UIList):
	def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
		object = data
		row = layout.row(align=True)
		sub=row.row(align=True)
		sub.scale_x = 0.65
		sub.label(text="%d" % (index))

		sub=row.row(align=True)
		sub.scale_x = 0.25
		sub.prop(item.Lumiere,"light_color",text='')

		sub=row.row(align=True)
		sub.scale_x = 1.75
		sub.prop(item,"name",text='')

		sub=row.row(align=True)
		sub.prop(item,"hide_viewport",text='')

		sub=row.row(align=True)
		sub.prop(item,"hide_render",text='')

# -------------------------------------------------------------------- #
## CREATE LIGHT
class CREATE_LIGHT_PT_Lumiere(Panel):
	bl_idname = "CREATE_LIGHT_PT_Lumiere"
	bl_label = "Light:"
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = "Lumiere"
	bl_context = "objectmode"

	@classmethod
	def poll(cls, context):
		primary_col, light_col, platform_col = get_collection()
		if primary_col:
			if light_col:
				if  ((len(context.selected_objects)==0) or context.view_layer.objects.active.name not in light_col.all_objects):
					return context.scene.Lumiere.create_menu=="Light"
				else:
					return False
		return context.scene.Lumiere.create_menu=="Light"

	def draw_header_preset(self, context):
		layout = self.layout
		col = layout.column(align=False)
		row = col.row(align=True)
		row.prop(context.scene.Lumiere, "create_menu", text="", expand=True)

	def draw(self, context):
		primary_col, light_col, platform_col = get_collection()
		layout = self.layout
		layout.use_property_split = True # Active single-column layout
		layout.use_property_decorate = False  # No animation.
		flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=True)
		col = flow.column(align=False)
		col.ui_units_x = 7
		col.prop(context.scene.Lumiere, "light_type",  text="", expand=False)
		col.separator()
		op = col.operator("lumiere.ray_operator", text="Add light", icon='BLANK1')
		op.light_type = context.scene.Lumiere.light_type
		op.arg = "Interactive lighting"
		op.operation = "create"
		col = flow.column(align=False)
		row = col.row(align=True)
		col.template_list("LIGHTS_UL_list", "", light_col, "all_objects", context.scene, "Lumiere_lights_list_index", rows=2)

# -------------------------------------------------------------------- #
## Parent panel
class POLL_PT_Lumiere:
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"

	@classmethod
	def poll(cls, context):
		primary_col, light_col, platform_col = get_collection()

		if primary_col:
			if (len(context.selected_objects)>0):
				if light_col and len(light_col.objects) > 0 :
					return context.view_layer.objects.active.name in light_col.all_objects
			else:
				return False
		return False

# -------------------------------------------------------------------- #
class MAIN_PT_Lumiere(POLL_PT_Lumiere, Panel):
	bl_idname = "MAIN_PT_Lumiere"
	bl_label = "Light:"
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = "Lumiere"
	bl_context = "objectmode"

	def draw_header_preset(self, context):
		scene = context.scene
		layout = self.layout
		col = layout.column(align=False)
		row = col.row(align=True)
		row.prop(scene.Lumiere, "create_menu", text="", expand=True)

	@classmethod
	def poll(cls, context):
		if (POLL_PT_Lumiere.poll(context)) :
			return context.scene.Lumiere.create_menu=="Light"

	def draw(self, context):
		light = context.active_object

		layout = self.layout
		layout.use_property_split = True # Active single-column layout
		layout.use_property_decorate = False  # No animation.
		flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=True)
		col = flow.column(align=False)
		col.ui_units_x = 7

		row = col.row(align=True)
		if bpy.context.scene.render.engine != 'CYCLES' and context.view_layer.objects.active.type == 'MESH' :
			row.alert = True
			row.label(text="Softbox not working in EEVEE")
			row.alert = False
			row = col.row(align=True)
		row.enabled = False if (light.Lumiere.ratio \
		and light.Lumiere.light_type in ("Softbox")) else True
		row.prop(light.Lumiere, "energy", text="Energy", slider = True)
		col.prop(light.Lumiere, "light_type", text="Light type")
		row = col.row(align=True)
		row.prop(light.Lumiere, "reflect_angle", text="Position")
		if light.Lumiere.reflect_angle == "Estimated":
			row.prop(light.Lumiere, "auto_bbox_center", text="", emboss=True, icon='AUTO')
			if light.Lumiere.auto_bbox_center:
				row = col.row(align=True)
				row.prop(light.Lumiere, "estimated_type", text="Center", emboss=True, icon='AUTO')
		row = col.row(align=True)
		row.prop(light.Lumiere, "invert_ray_cast", text="Invert")

# -------------------------------------------------------------------- #
## Softbox Sub panel
class MESH_OPTIONS_PT_Lumiere(POLL_PT_Lumiere, Panel):
	bl_idname = "MESH_OPTIONS_PT_Lumiere"
	bl_label = "Options"
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = "Lumiere"
	bl_context = "objectmode"

	@classmethod
	def poll(cls, context):
		if (POLL_PT_Lumiere.poll(context)) and context.scene.Lumiere.create_menu=="Light" :
			return context.view_layer.objects.active.type == 'MESH'

	def draw_header_preset(self, context):
		light = context.active_object
		layout = self.layout
		col = layout.column(align=False)
		if light_in_scene(context):
			row = col.row(align=True)
			op = row.operator("lumiere.ray_operator", text="", emboss=False, icon="MOUSE_LMB_DRAG")
			op.arg = "Interactive lighting"
			op.operation = "ray_cast"
			row.separator()
		row.prop(light.Lumiere, "select_only", text="", icon='VIS_SEL_11' if light.Lumiere.select_only else 'VIS_SEL_01')

	def draw(self, context):
		light = context.active_object
		mat = get_mat_name(light)

		layout = self.layout
		layout.use_property_split = True # Active single-column layout
		layout.use_property_decorate = False  # No animation.
		flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=True)
		col = flow.column(align=False)
		col.ui_units_x = 7
		col.prop(light.Lumiere, "target", text="Target")
		col.prop(light.Lumiere, "range", text="Range")

		col = flow.column(align=False)
		col.ui_units_x = 7
		if light.Lumiere.lock_scale:
			row = col.row(align=True)
			row.prop(light.Lumiere, "scale_xy", text="Scale xy")
			row.prop(light.Lumiere, "lock_scale", text="", emboss=False, icon='DECORATE_LOCKED')

		if not light.Lumiere.lock_scale:
			row = col.row(align=True)
			row.prop(light.Lumiere, "scale_x", text="Scale X")
			row.prop(light.Lumiere, "lock_scale", text="", emboss=False, icon='DECORATE_UNLOCKED')
			row = col.row(align=True)
			row.prop(light.Lumiere, "scale_y", text="Scale Y")
			row.prop(light.Lumiere, "lock_scale", text="", emboss=False, icon='DECORATE_UNLOCKED')
		row = col.row(align=True)
		row.prop(light.Lumiere, "ratio", text="Keep ratio")

		col.separator()
		col2 = flow.column(align=True)
		if light.Lumiere.lock_img == True :
			row = col.row(align=True)
			row.prop(context.scene.Lumiere, "link_to_light", text="Unlock to use:")
			col2.enabled = False
		col2.prop(light.Lumiere, "rotation", text="Rotation")
		col2.prop(light.Lumiere, "spin", text="Spin")
		col2.prop(light.Lumiere, "tilt", text="Tilt")
		col2.separator()

		col = flow.column(align=False)
		col.ui_units_x = 7
		col = col.column(align=True)
		col.prop(light.Lumiere, "softbox_rounding", text="Round Shape")
		col.prop(light.modifiers["Bevel"], "segments", text="Segments", slider=False)
		col.separator()

		soft_edges1 = mat.node_tree.nodes["Edges ColRamp"].color_ramp.elements[0]
		soft_edges2 = mat.node_tree.nodes["Edges ColRamp"].color_ramp.elements[1]
		edges_value = mat.node_tree.nodes["Edges value"].outputs[0]
		col = col.column(align=True)
		col.prop(edges_value, "default_value", text="Soft edges", slider=False)
		row = col.row(align=True)
		row.prop(soft_edges1, "position", text='Edges')
		row.prop(soft_edges2, "position", text='')
		col.separator()

# -------------------------------------------------------------------- #
class MESH_MATERIALS_PT_Lumiere(POLL_PT_Lumiere, Panel):
	bl_idname = "MESH_MATERIALS_PT_Lumiere"
	bl_label = " "
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = "Lumiere"
	bl_context = "objectmode"

	@classmethod
	def poll(cls, context):
		if (POLL_PT_Lumiere.poll(context)) and context.scene.Lumiere.create_menu=="Light" :
			return context.view_layer.objects.active.type == 'MESH'

	def draw_header_preset(self, context):
		light = context.active_object
		layout = self.layout
		layout.label(text=(light.Lumiere.material_menu).title())
		col = layout.column(align=False)
		col.alignment = 'LEFT'
		row = col.row(align=True)
		row.prop(light.Lumiere, "material_menu", text="", expand=True)
		row.separator()

	def draw(self, context):
		light = context.active_object
		mat = get_mat_name(light)
		colramp = mat.node_tree.nodes['ColorRamp']
		img_texture = mat.node_tree.nodes["Image Texture"]
		invert = mat.node_tree.nodes["Texture invert"].inputs[0]
		falloff = mat.node_tree.nodes["Light Falloff"].inputs[1]

		layout = self.layout
		layout.use_property_split = True # Active single-column layout
		layout.use_property_decorate = False  # No animation.
		flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=True)
		col = layout.column(align=False)
		col = col.column(align=False)
		#--CYCLES
		if light.Lumiere.material_menu == 'Color':
			col.prop(light.Lumiere, "color_type", text="", )
			if light.Lumiere.color_type in ('Color', 'Reflector'):
				col.prop(light.Lumiere, "light_color", text="Color")

			elif light.Lumiere.color_type == 'Linear':
				col.prop(light.Lumiere, "rotate_ninety", text="Rotate 90°", icon="FILE_REFRESH")
				col.template_color_ramp(colramp, "color_ramp", expand=True)
			elif light.Lumiere.color_type == 'Spherical':
				col.template_color_ramp(colramp, "color_ramp", expand=True)
			elif light.Lumiere.color_type == 'Blackbody':
				col.prop(light.Lumiere, "blackbody", text="Temperature", expand=True)

		elif light.Lumiere.material_menu == 'Texture':
			row = col.row(align=True)
			row.prop_search(light.Lumiere, "img_name", bpy.data, "images", text="")
			row.operator("image.open",text='', icon='FILEBROWSER')
			col.prop(light.Lumiere, "img_scale", text="Scale")
			col.prop(invert, "default_value", text="Invert")
			col.prop(img_texture, "extension", text="Repeat")
			col.prop(light.Lumiere, "img_reflect_only", text="Reflection only")

		elif light.Lumiere.material_menu == 'IES':
			row = col.row(align=True)
			row.prop_search(light.Lumiere, "ies_name", bpy.data, "texts", text="", icon="OUTLINER_OB_LIGHT")
			op = row.operator("text.open", text='', icon='FILEBROWSER')
			op.filter_python = False
			op.filter_text = False
			op.filter_folder = False
			col.prop(light.Lumiere, "ies_scale", text="Scale")
			col.prop(light.Lumiere, "ies_reflect_only", text="Reflection only")

		elif light.Lumiere.material_menu == 'Options':
			col.prop(light.Lumiere, "falloff_type", text="Falloff")
			col.prop(light.Lumiere, "falloff_strength", text="Strength")
			col.prop(falloff, "default_value", text="Smooth")
			col.prop(mat.cycles, "sample_as_light", text='MIS')

# -------------------------------------------------------------------- #
## Lamp Sub panel

class LAMP_OPTIONS_PT_Lumiere(POLL_PT_Lumiere, Panel):
	bl_idname = "LAMP_OPTIONS_PT_Lumiere"
	bl_label = "Options"
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = "Lumiere"
	bl_context = "objectmode"

	@classmethod
	def poll(cls, context):
		if (POLL_PT_Lumiere.poll(context)) and context.scene.Lumiere.create_menu=="Light" :
			return context.view_layer.objects.active.type == 'LIGHT'

	def draw_header_preset(self, context):
		light = context.active_object
		layout = self.layout
		col = layout.column(align=False)
		row = col.row(align=True)
		if light_in_scene(context):
			row = col.row(align=True)
			op = row.operator("lumiere.ray_operator", text="", emboss=False, icon="MOUSE_LMB_DRAG")
			op.arg = "Interactive lighting"
			op.operation = "ray_cast"
			row.separator()
		row.prop(light.Lumiere, "select_only", text="", icon='VIS_SEL_11' if light.Lumiere.select_only else 'VIS_SEL_01')
		row.separator()

	def draw(self, context):
		light = context.active_object
		mat = get_mat_name(light)

		layout = self.layout
		layout.use_property_split = True # Active single-column layout
		layout.use_property_decorate = False  # No animation.
		flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=True)
		col = flow.column(align=False)
		col.ui_units_x = 7
		col = col.column(align=False)
		col.prop(light.Lumiere, "target", text="Target")
		col.prop(light.Lumiere, "range", text="Range")

		col.separator()

		col = flow.column(align=False)
		col.ui_units_x = 7
		col = col.column(align=True)

		if light.data.type == "AREA":
			col.prop(light.data, "shape", text="Shape")
			col = col.column(align=True)
			row = col.row(align=True)
			if light.data.shape in ('SQUARE', 'DISK'):
				row.prop(light.Lumiere, "scale_xy", text="Scale xy")
			else:
				if light.Lumiere.lock_scale:
					row.prop(light.Lumiere, "scale_xy", text="Scale xy")
					row.prop(light.Lumiere, "lock_scale", text="", emboss=False, icon='DECORATE_LOCKED')

				else:
					row = col.row(align=True)
					row.prop(light.Lumiere, "scale_x", text="Scale X")
					row.prop(light.Lumiere, "lock_scale", text="", emboss=False, icon='DECORATE_UNLOCKED')
					row = col.row(align=True)
					row.prop(light.Lumiere, "scale_y", text="Scale Y")
					row.prop(light.Lumiere, "lock_scale", text="", emboss=False, icon='DECORATE_UNLOCKED')

		elif light.data.type == "SPOT":
			col.prop(light.data, "spot_size", text="Cone Size")
			col.prop(light.data, "spot_blend", text="Cone Blend")
			col.prop(light.Lumiere, "scale_xy", text="Shadow")

		elif light.data.type == "POINT":
			col.prop(light.Lumiere, "scale_xy", text="Shadow")

		elif light.data.type == "SUN":
			col.prop(light.Lumiere, "scale_xy", text="Shadow")

		col.separator()
		col = flow.column(align=False)
		col.ui_units_x = 7
		col2 = flow.column(align=True)
		if light.Lumiere.lock_img == True :
			row = col.row(align=True)
			row.prop(context.scene.Lumiere, "link_to_light", text="Unlock to use:")
			col2.enabled = False
		col2.prop(light.Lumiere, "rotation", text="Rotation")
		col2.prop(light.Lumiere, "spin", text="Spin")
		col2.prop(light.Lumiere, "tilt", text="Tilt")
		col2.separator()
# -------------------------------------------------------------------- #
class LAMP_MATERIALS_PT_Lumiere(POLL_PT_Lumiere, Panel):
	bl_idname = "LAMP_MATERIALS_PT_Lumiere"
	bl_label = " "
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = "Lumiere"
	bl_context = "objectmode"

	@classmethod
	def poll(cls, context):
		if (POLL_PT_Lumiere.poll(context)) and context.scene.Lumiere.create_menu=="Light":
			return context.view_layer.objects.active.type == 'LIGHT'

	def draw_header_preset(self, context):
		light = context.active_object
		layout = self.layout
		layout.label(text=(light.Lumiere.material_menu).title())
		col = layout.column(align=False)
		row = col.row(align=True)
		# if bpy.context.scene.render.engine == 'CYCLES':
		row.prop(light.Lumiere, "material_menu", text="", expand=True)
		row.separator()

	def draw(self, context):
		light = context.active_object
		ies = light.data.node_tree.nodes["IES"]
		colramp = light.data.node_tree.nodes["ColorRamp"]
		img_texture = light.data.node_tree.nodes["Image Texture"]
		falloff = light.data.node_tree.nodes["Light Falloff"].inputs[1]

		layout = self.layout
		layout.use_property_split = True # Active single-column layout
		layout.use_property_decorate = False  # No animation.
		flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=True)
		col = flow.column(align=False)
		col.ui_units_x = 7
		col = col.column()
		if bpy.context.scene.render.engine != 'CYCLES':
			#--EEVEE
			if light.Lumiere.material_menu == 'Color':
				col.prop(light.Lumiere, "light_color", text="Color")
			elif light.Lumiere.material_menu == 'Options':
				layout = self.layout
				if float(bpy.app.version_string[:3]) > 2.8:
					col = layout.column(heading="Shadows")
					col.prop(light.data, "use_shadow", text="")
				else:
					col.prop(light.data, "use_shadow", text="Shadows")

				col = layout.column()
				col.active = light.data.use_shadow
				if light.data.type != 'SUN':
					col.prop(light.data, "shadow_buffer_clip_start", text="Clip Start")
				col.prop(light.data, "shadow_buffer_bias", text="Bias")
				col.prop(light.data, "use_contact_shadow", text="Contact shadows")
				col = layout.column()
				col.active = light.data.use_contact_shadow
				col.prop(light.data, "contact_shadow_distance", text="Distance")
				col.prop(light.data, "contact_shadow_bias", text="Bias")
				col.prop(light.data, "contact_shadow_thickness", text="Thickness")

		else:
			#--CYCLES
			if light.Lumiere.material_menu == "Texture":
				row = col.row(align=True)
				row.prop_search(light.Lumiere, "img_name", bpy.data, "images", text="")
				row.operator("image.open",text='', icon='FILEBROWSER')
				col = col.column(align=True)
				row = col.row(align=True)
				row.prop(light.Lumiere, "img_scale", text="Scale")
				row = col.row(align=True)
				row.prop(light.Lumiere, "img_invert", text="Invert")
				row = col.row(align=True)
				row.prop(img_texture, "extension", text="Repeat")

			elif light.Lumiere.material_menu == 'IES':
				row = col.row(align=True)
				row.prop_search(light.Lumiere, "ies_name", bpy.data, "texts", text="", icon="OUTLINER_OB_LIGHT")
				op = row.operator("text.open", text='', icon='FILEBROWSER')
				op.filter_python = False
				op.filter_text = False
				op.filter_folder = False
				col.prop(light.Lumiere, "ies_scale", text="Scale")
			elif light.Lumiere.material_menu == 'Color':
				col.prop(light.Lumiere, "color_type", text="", )

				if light.Lumiere.color_type == 'Color':
					col = col.column(align=False)
					col.prop(light.Lumiere, "light_color", text="Color")
				elif light.Lumiere.color_type == 'Blackbody':
					col = col.column(align=False)
					col.prop(light.Lumiere, "blackbody", text="Temperature")

				elif light.Lumiere.color_type == 'Gradient':
					col.template_color_ramp(colramp, "color_ramp", expand=True)

			elif light.Lumiere.material_menu == 'Options':
				if light.data.type != "SUN":
					col.prop(light.Lumiere, "falloff_type", text="Falloff")
					col.prop(light.Lumiere, "falloff_strength", text="Strength")
					col.prop(falloff, "default_value", text="Smooth")
					col.separator()
				flow = col.column_flow()
				flow.prop(light.data.cycles, "cast_shadow", text='Shadow')
				flow.prop(light.data.cycles, "use_multiple_importance_sampling", text='MIS')
				flow.prop(light.cycles_visibility, "diffuse", text='Diffuse')
				flow.prop(light.cycles_visibility, "glossy", text='Specular')

# -------------------------------------------------------------------- #
# Utils
def light_in_scene(context):
	primary_col, light_col, platform_col = get_collection()

	if (context.active_object is not None) and light_col is not None and len(light_col.objects) > 0:
		return True
	else:
		return False
# -------------------------------------------------------------------- #
## Register
classes = [
	Lumiere_main_prop,
	Lumiere_lights_prop,
	LIGHTS_UL_list,
	MAIN_PT_Lumiere,
	MESH_OPTIONS_PT_Lumiere,
	MESH_MATERIALS_PT_Lumiere,
	LAMP_OPTIONS_PT_Lumiere,
	LAMP_MATERIALS_PT_Lumiere,
	CREATE_LIGHT_PT_Lumiere,
	Lumiere_ui_lights_Prop,
	Lumiere_group_prop,
	]


def register():
	from bpy.utils import register_class
	for cls in classes:
		register_class(cls)
	# bpy.app.handlers.frame_change_post.append(anim)
	bpy.types.Object.Lumiere = bpy.props.PointerProperty(type=Lumiere_lights_prop)
	bpy.types.Scene.Lumiere = bpy.props.PointerProperty(type=Lumiere_main_prop)

	bpy.types.Scene.Lumiere_lights_list = bpy.props.CollectionProperty(type=Lumiere_ui_lights_Prop)
	bpy.types.Scene.Lumiere_lights_list_index = bpy.props.IntProperty(name = "Index", default = 0, update=update_uilist)


def unregister():
	from bpy.utils import unregister_class
	for cls in reversed(classes):
		unregister_class(cls)
	# bpy.app.handlers.frame_change_post.remove(anim)
	del bpy.types.Scene.Lumiere
	del bpy.types.Object.Lumiere
	del bpy.types.Scene.Lumiere_lights_list
	del bpy.types.Scene.Lumiere_lights_list_index
