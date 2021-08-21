import bpy
import os
import json
import sys
from bpy_extras import view3d_utils
from .lumiere_utils import (
	get_mat_name,
	raycast_light,
	raycast_shadow,
	export_props_light,
	export_props_group,
	get_lumiere_dict,
	update_lumiere_dict,
	cartesian_coordinates,
	setSunPosition,
	get_collection,
	create_collections,
	get_preferences,
	)

from .lumiere_draw import (
	draw_callback_lumiere,
	draw_callback_2d,
	draw_callback_3d,
	)

from .lights.lumiere_lights import (
	create_softbox,
	create_lamp,
	)

from .platform.lumiere_platform import(
	create_platform,
	)

from bpy.types import (
	Operator,
	Menu,
	)

from mathutils import (
	Vector,
	)

from mathutils.geometry import intersect_line_plane

from math import (
	isnan,
	degrees,
	tan,
	cos,
	)

# -------------------------------------------------------------------- #
class LUMIERE_OT_export_light(Operator):
	"""Export the current light data in JSON format"""

	bl_idname = "object.export_light"
	bl_label = "Export light"

	name : bpy.props.StringProperty()

	def execute(self, context):
		current_file_path = __file__
		current_file_dir = os.path.dirname(__file__)
		light = context.active_object
		light_selected = []

	#---Try to open the Lumiere export dictionary
		try:
			with open(current_file_dir + "\\" + "lumiere_dictionary.json", 'r', encoding='utf-8') as file:
				my_dict = json.load(file)
				file.close()
		except Exception:
			print("Warning, dict empty, creating a new one.")
			my_dict = {}

		for obj in context.view_layer.objects.selected:
			if obj in list(context.scene.collection.children['Lumiere'].objects):
				light_selected.append(obj)

		if len(light_selected) > 1:
			lumiere_dict = export_props_group(self, context, self.name, light_selected)
		else:
			lumiere_dict = export_props_light(self, context, light)

		my_dict.update(lumiere_dict)

		with open(current_file_dir + "\\" + "lumiere_dictionary.json", "w", encoding='utf-8') as file:
			json.dump(my_dict, file, sort_keys=True, indent=4, ensure_ascii=False)

		file.close()
		message = "Light exported"
		self.report({'INFO'}, message)
		return {'FINISHED'}


# -------------------------------------------------------------------- #
class LUMIERE_OT_light_spot(Operator):
	bl_idname = "lumiere.light_spot"
	bl_label = "Light operator"
	bl_description = "Light spot"
	bl_options = {'REGISTER', 'UNDO'}

	action : bpy.props.StringProperty()
	arg: bpy.props.StringProperty()

	@classmethod
	def description(cls, context, properties):
		return properties.arg

	def invoke(self, context, event):
		self.init_mouse_x = event.mouse_x
		self.init_mouse_y = event.mouse_y

		light = context.object
		if event.type == 'LEFTMOUSE':
			self.init_value = self.save_value = light.data.spot_size
			context.window_manager.modal_handler_add(self)
			return {"RUNNING_MODAL"}
		return {'FINISHED'}

	def modal(self, context, event):
		light = context.object
		if "MOUSEMOVE" in event.type :
			delta_x = (event.mouse_x - self.init_mouse_x) / 50.0
			light.data.spot_size = self.init_value + delta_x
			return {"RUNNING_MODAL"}

		elif event.type == "RIGHTMOUSE":
			light.Lumiere.spot_size = self.save_value
			return {'CANCELLED'}

		else:
			return {'FINISHED'}

		return {'FINISHED'}
# -------------------------------------------------------------------- #
def status_bar_draw(self, context):
	layout = self.layout
	layout.label(text="Modal", icon="MOUSE_LMB_DRAG")
	layout.label(text="Confirm", icon="MOUSE_RMB")
	layout.label(text="", icon="MOUSE_LMB")
	layout.label(text="Target", icon="EVENT_T")
	layout.label(text="", icon="EVENT_R")
	layout.label(text="Range", icon="MOUSE_MOVE")
	layout.label(text="", icon="EVENT_E")
	layout.label(text="Energy", icon="MOUSE_MOVE")

# -------------------------------------------------------------------- #
class LUMIERE_OT_ray_operator(Operator):
	bl_idname = "lumiere.ray_operator"
	bl_label = "Lighting operator"
	bl_description = "Interactive lighting mode"
	bl_options = {'REGISTER', 'UNDO'}

	action : bpy.props.StringProperty()
	shadow : bpy.props.BoolProperty()
	light_type : bpy.props.StringProperty()
	arg: bpy.props.StringProperty()
	operation: bpy.props.StringProperty()

	@classmethod
	def description(cls, context, properties):
		return "Click to enter: " + properties.arg

	@classmethod
	def poll(cls, context):
		return context.area.type == 'VIEW_3D' and context.mode == 'OBJECT'

	def __init__(self):
		self.light_selected = False
		if self.action == "shadow":
			self.shadow = True
		else:
			self.shadow = False
		self.is_running = False
		self.lmb = False
		self.draw_handle_2d = None
		self.draw_handle_3d = None
		self.point = False
		self.energy = False
		self.range = False
		create_collections(self)

	def invoke(self, context, event):
		self.light = context.object
		args = (self, context)
		self.addon_prefs = get_preferences()
		self.lumiere_context = context
		if context.space_data.type == 'VIEW_3D':
			self.lumiere_area = context.area
		self.enable_cursor = context.space_data.overlay.show_cursor
		self.enable_navigate = context.space_data.show_gizmo_navigate
		self.enable_tool = context.space_data.show_gizmo_tool
		self.relat_lines = context.space_data.overlay.show_relationship_lines

		self.status_old = bpy.types.STATUSBAR_HT_header.draw
		bpy.types.STATUSBAR_HT_header.draw = status_bar_draw
		self.register_handlers(args, context)
		context.window_manager.modal_handler_add(self)
		return {"RUNNING_MODAL"}

	def register_handlers(self, args, context):
		if self.is_running == False:
			self.is_running = True
			context.scene.is_running = True

			self.draw_handle_2d = bpy.types.SpaceView3D.draw_handler_add(draw_callback_2d, args, "WINDOW", "POST_PIXEL")
			self.draw_handle_3d = bpy.types.SpaceView3D.draw_handler_add(draw_callback_3d, args, "WINDOW", "POST_VIEW")

	def unregister_handlers(self, context):
		context.workspace.status_text_set(None)
		bpy.types.STATUSBAR_HT_header.draw = self.status_old
		bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle_2d, "WINDOW")
		bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle_3d, "WINDOW")
		self.draw_handle_2d = None
		self.draw_handle_3d = None
		context.scene.is_running = False

		if context.view_layer.active_layer_collection.name == "Lumiere":
			context.view_layer.active_layer_collection = context.view_layer.layer_collection

	def modal(self, context, event):

		# Prevent exceptions when switching workspaces
		if not hasattr(context.area, 'regions'):
			self.is_running = False
			self.unregister_handlers(context)
			return {'CANCELLED'}

		# Find the limit of the view3d region
		check_region(self,context,event)

		# Hide 3d cursor
		if self.in_view_3d:
			context.space_data.overlay.show_cursor = False
			context.space_data.show_gizmo_navigate = False
			context.space_data.show_gizmo_tool = False
			context.space_data.overlay.show_relationship_lines = False

		try:

			if context.area != self.lumiere_area:
				self.is_running = False
				self.unregister_handlers(context)
				return {'CANCELLED'}

			if event.type in {"ESC", "RIGHTMOUSE"} :
				self.unregister_handlers(context)

				# State of 3d cursor before Lumiere
				context.space_data.overlay.show_cursor = self.enable_cursor
				context.space_data.show_gizmo_navigate = self.enable_navigate
				context.space_data.show_gizmo_tool = self.enable_tool
				context.space_data.overlay.show_relationship_lines = self.relat_lines
				self.is_running = False

				return {'CANCELLED'}

			# Left mouse button press
			elif event.type == 'LEFTMOUSE' and self.in_view_3d:
				self.lmb = event.value == 'PRESS'

			# Allow navigation
			elif event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'} or event.type.startswith("NUMPAD"):
				return {'PASS_THROUGH'}

			if self.addon_prefs.modal_keys:
				if event.type == 'T':
					self.point = event.value == 'PRESS'

				if event.type == 'R':
					self.range = event.value == 'PRESS'

				if event.type == 'E':
					self.energy = event.value == 'PRESS'

			# Left mouse button pressed with an object from Lumiere collection
			if self.lmb and self.in_view_3d:

				context.scene.cycles.preview_pause = self.addon_prefs.render_pause
				if self.action == "shadow":
					self.shadow_hit = Vector(bpy.context.active_object.Lumiere.hit).copy()
					raycast_shadow(self, event, context, context.object.Lumiere.range, shadow_hit=self.shadow_hit)

				else:
					# Raycast to move the light compared to the targeted object
					if self.operation == "ray_cast":
						raycast_light(self, event, context, self.light.Lumiere.range)

					elif self.operation == "create":
						if self.light_type == "Softbox":
							create_softbox()
						else:
							create_lamp(type = self.light_type)
						# Go back to the ray_cast operator
						self.light = context.object
						self.operation = "ray_cast"

			elif self.energy and self.in_view_3d:
				self.light.Lumiere.energy += (event.mouse_x - event.mouse_prev_x)

			elif self.range and self.in_view_3d:
				self.light.Lumiere.range += (event.mouse_x - event.mouse_prev_x) * .1

			else:
				if self.addon_prefs.render_pause:
					context.scene.cycles.preview_pause = False
					# Hack to update cycles
					context.view_layer.objects.active = self.light
				return {'PASS_THROUGH'}
			return {"RUNNING_MODAL"}

		except:
			print("\n[Lumiere ERROR]\n")
			import traceback
			traceback.print_exc()
			self.unregister_handlers(context)

			self.report({'WARNING'},
						"Operation finished. (Check the console for more info)")

			return {'FINISHED'}

	def finish(self):
		return {"FINISHED"}


# Utilities
###############################################
# Get the region area where the operator is used
def check_region(self,context,event):

	try:
		self.in_view_3d = False

		for area in context.screen.areas:
			if area.type == "VIEW_3D" :
				for region in context.area.regions:
					if region.type == "TOOLS":
						t_panel = region
					elif region.type == "UI":
						ui_panel = region

				view_3d_region_x = Vector((context.area.x + t_panel.width, context.area.x + context.area.width - (ui_panel.width+1)))
				view_3d_region_y = Vector((context.region.y, context.region.y + context.region.height))

				if (event.mouse_x > view_3d_region_x[0] and event.mouse_x < view_3d_region_x[1] \
				and event.mouse_y > view_3d_region_y[0] and event.mouse_y < view_3d_region_y[1]):
					self.in_view_3d = True
					return True

	except:
		print("\n[Lumiere ERROR]\n")
		import traceback
		traceback.print_exc()
		self.unregister_handlers(context)

		self.report({'WARNING'},
					"Operation finished. (Check the console for more info)")

# -------------------------------------------------------------------- #
class LUMIERE_OT_Platform(Operator):
	"""Create Lumiere_platforms_prop"""
	bl_idname = "lumiere.platform_operator"
	bl_label = "Platform operator"
	bl_description = "Create a new platform"
	bl_options = {'REGISTER', 'UNDO'}

	def __init__(self):
		create_collections(self)

	def execute(self, context):
		primary_col, light_col, platform_col = get_collection()

		if platform_col :
			create_platform()

		return {'FINISHED'}

# -------------------------------------------------------------------- #
class LUMIERE_OT_dialog(Operator):
	"""Tooltip"""
	bl_idname = "lumiere.dialog_operator"
	bl_label = "Tooltip operator"

	action : bpy.props.StringProperty()
	arg: bpy.props.StringProperty()
	operation : bpy.props.StringProperty()

	@classmethod
	def description(cls, context, props):
		return props.arg

	@classmethod
	def poll(cls, context):
		return context.active_object is not None

	def execute(self, context):
		return {'FINISHED'}

	def invoke(self, context, event):
		wm = context.window_manager
		return wm.invoke_popup(self, width=100)

	def draw(self, context):
		obj = context.active_object
		layout = self.layout
		if getattr(obj, self.operation).bl_rna.properties[self.action].type == 'FLOAT':
			layout.prop(getattr(obj, self.operation), self.action)
		elif getattr(obj, self.operation).bl_rna.properties[self.action].type == 'ENUM':
			layout.props_enum(getattr(obj, self.operation), self.action)

# -------------------------------------------------------------------- #
## Register

classes = [
	LUMIERE_OT_export_light,
	LUMIERE_OT_ray_operator,
	LUMIERE_OT_Platform,
	LUMIERE_OT_dialog,
	LUMIERE_OT_light_spot,
	]

def register():
	from bpy.utils import register_class
	for cls in classes:
		register_class(cls)
	bpy.types.Scene.is_running = bpy.props.BoolProperty(default=False)

def unregister():
	from bpy.utils import unregister_class
	for cls in reversed(classes):
		unregister_class(cls)
	del bpy.types.Scene.is_running
