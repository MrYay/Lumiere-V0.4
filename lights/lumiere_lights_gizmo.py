import bpy
from mathutils import (
	Matrix,
	Vector,
	)

from math import (
	degrees,
	radians,
	sqrt,
	atan,
	cos,
	)

from bpy.types import (
	GizmoGroup,
	Gizmo,
	Operator,
	)

from ..lumiere_utils import (
	get_collection,
	get_package,
	raycast_light,
	get_preferences,
	create_2d_gizmo,
	)

from ..lumiere_draw import (
	draw_gizmo_2d_label,
	draw_highlight_gizmo,
	)

# -------------------------------------------------------------------- #
def status_bar_draw(self, context):
	layout = self.layout
	layout.label(text="Update", icon="MOUSE_MOVE")
	layout.label(text="Confirm", icon="MOUSE_LMB")
	layout.label(text="Cancel", icon="MOUSE_RMB")
	layout.label(text="Precise", icon="EVENT_SHIFT")

# -------------------------------------------------------------------- #
class LUMIERE_OT_2dgizmo_light(Operator):
	bl_idname = "lumiere.2dgizmo_light"
	bl_label = "2d gizmo operator"
	bl_description = "2d gizmo operator"
	bl_options = {'GRAB_CURSOR', 'BLOCKING'}

	action : bpy.props.StringProperty()
	arg: bpy.props.StringProperty()

	@classmethod
	def description(cls, context, properties):
		return properties.arg

	def unregister_handlers(self, context):
		context.workspace.status_text_set(None)
		bpy.types.STATUSBAR_HT_header.draw = self.status_old
		bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle_2d, "WINDOW")
		self.draw_handle_2d = None

	def invoke(self, context, event):
		self.init_mouse_x = event.mouse_x
		self.init_mouse_y = event.mouse_y
		self.status_old = bpy.types.STATUSBAR_HT_header.draw

		light = context.object
		if event.type == 'LEFTMOUSE':
			# None modal action
			if self.action == "select_only":
				light.Lumiere.select_only = not light.Lumiere.select_only
			else:
				if self.action in ["spot_size", "spot_blend"]:
					self.init_value = self.save_value = getattr(light.data, self.action)
				else:
					self.init_value = self.save_value = getattr(light.Lumiere, self.action)

				bpy.types.STATUSBAR_HT_header.draw = status_bar_draw
				context.window_manager.modal_handler_add(self)
				self.draw_handle_2d = bpy.types.SpaceView3D.draw_handler_add(draw_gizmo_2d_label, (self, context,self.action, "light"), "WINDOW", "POST_PIXEL")
				return {"RUNNING_MODAL"}

		return {'FINISHED'}

	def modal(self, context, event):
		light = context.object
		shift_press = event.shift and event.value == 'PRESS'
		accuracy = 200 if shift_press else 50

		if "MOUSEMOVE" in event.type :
			accuracy = 50 if shift_press else 10
			delta_x = (event.mouse_x - self.init_mouse_x) / accuracy

			if self.action in ["spot_size", "spot_blend"]:
				setattr(light.data, self.action, self.init_value + delta_x)
			else:
				setattr(light.Lumiere, self.action, self.init_value + delta_x)

			return {"RUNNING_MODAL"}

		elif event.type == "RIGHTMOUSE":
			setattr(light.Lumiere, self.action, self.save_value)
			if self.draw_handle_2d is not None:
				self.unregister_handlers(context)
			return {'CANCELLED'}

		elif "SHIFT" in event.type :
			return {'PASS_THROUGH'}

		if self.draw_handle_2d is not None:
			self.unregister_handlers(context)
		return {'FINISHED'}

# -------------------------------------------------------------------- #
# LIGHTS 2D Gizmos
class LUMIERE_GGT_2dgizmo_light(GizmoGroup):
	bl_idname = "LUMIERE_GGT_2dgizmo_light"
	bl_label = "Lumiere shade smooth 2dwidget"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'WINDOW'
	bl_options = {'PERSISTENT', 'SCALE', 'SHOW_MODAL_ALL', 'SELECT'}

	@classmethod
	def poll(cls, context):
		light = context.object
		primary_col, light_col, platform_col = get_collection()
		if context.active_object:
			if light_col and len(light_col.objects) > 0 :
				return context.view_layer.objects.active.name in light_col.all_objects and light.mode == 'OBJECT'
		else:
			return False

	def __init__(self):
		self.color_light = (0,0,0)
# -------------------------------------------------------------------- #
	def setup(self, context):
		light = context.object

		alpha = .8
		color = 0.2,0.2,0.2
		# color_menu = hex_to_rgb(0xEDB962)
		# color_menu = hex_to_rgb(0xC2A7C7)
		color_menu = hex_to_rgb(0xE7CFBC)
		color_enable = hex_to_rgb(0x9BBBE1)
		color_highlight = 0.5,0.5,0.5
		alpha_highlight = 1
		scale_basis = (80 * 0.35) / 2

		#-- Energy
		self.energy_2dwidget = create_2d_gizmo(self, context, "GIZMO_GT_button_2d", "LIGHT_SUN", alpha, color, color_highlight, alpha_highlight, scale_basis, operator = "2dgizmo_light", action = "energy", arg = "Adjust energy")

		#-- Range
		self.range_2dwidget = create_2d_gizmo(self, context, "GIZMO_GT_button_2d", "CON_TRACKTO", alpha, color, color_highlight, alpha_highlight, scale_basis, operator = "2dgizmo_light", action = "range", arg = "Adjust range")

		#-- Scale
		self.scale_2dwidget = create_2d_gizmo(self, context, "GIZMO_GT_button_2d", "FULLSCREEN_ENTER", alpha, color, color_highlight, alpha_highlight, scale_basis, operator = "2dgizmo_light", action = "scale_xy", arg = "Adjust scale")

		#-- Scale X
		self.scale_x_2dwidget = create_2d_gizmo(self, context, "GIZMO_GT_button_2d", "SORT_DESC", alpha, color, color_highlight, alpha_highlight, scale_basis, operator = "2dgizmo_light", action = "scale_x", arg = "Adjust scale X")

		#-- Scale Y
		self.scale_y_2dwidget = create_2d_gizmo(self, context, "GIZMO_GT_button_2d", "FORWARD", alpha, color, color_highlight, alpha_highlight, scale_basis, operator = "2dgizmo_light", action = "scale_y", arg = "Adjust scale Y")

		#-- Rotation
		self.rotation_2dwidget = create_2d_gizmo(self, context, "GIZMO_GT_button_2d", "FILE_REFRESH", alpha, color, color_highlight, alpha_highlight, scale_basis, operator = "2dgizmo_light", action = "rotation", arg = "Adjust rotation")

		#-- Spin
		self.spin_2dwidget = create_2d_gizmo(self, context, "GIZMO_GT_button_2d", "PHYSICS", alpha, color, color_highlight, alpha_highlight, scale_basis, operator = "2dgizmo_light", action = "spin", arg = "Adjust spin")

		#-- Tilt
		self.tilt_2dwidget = create_2d_gizmo(self, context, "GIZMO_GT_button_2d", "GIZMO", alpha, color, color_highlight, alpha_highlight, scale_basis, operator = "2dgizmo_light", action = "tilt", arg = "Adjust tilt")

		#-- Select Only
		self.select_only_2dwidget = create_2d_gizmo(self, context, "GIZMO_GT_button_2d", "VIS_SEL_11", alpha, color, color_enable, alpha_highlight, scale_basis, operator = "2dgizmo_light", action = "select_only", arg = "Enable select_only")

		#-- Light type
		self.light_type_2dwidget = create_2d_gizmo(self, context, "GIZMO_GT_button_2d", "LIGHT", alpha, color, color_menu, alpha_highlight, scale_basis, operator = "dialog_operator", action = "light_type", arg = "Select light type", operation = "Lumiere")

		#-- Spot size
		self.spot_size_2dwidget = create_2d_gizmo(self, context, "GIZMO_GT_button_2d", "LIGHT_SPOT", alpha, color, color_highlight, alpha_highlight, scale_basis, operator = "2dgizmo_light", action = "spot_size", arg = "Adjust spot_size")

		#-- Spot blend
		self.spot_blend_2dwidget = create_2d_gizmo(self, context, "GIZMO_GT_button_2d", "ANTIALIASED", alpha, color, color_highlight, alpha_highlight, scale_basis, operator = "2dgizmo_light", action = "spot_blend", arg = "Adjust spot_blend")

		#-- Raycast
		self.raycast_2dwidget = create_2d_gizmo(self, context, "GIZMO_GT_button_2d", "MOUSE_LMB_DRAG", alpha, color, color_enable, alpha_highlight, scale_basis, operator = "ray_operator", action = "raycast", arg = "Interactive lighting", operation = "ray_cast")

		#-- Color
		self.color_2dwidget = create_2d_gizmo(self, context, "GIZMO_GT_button_2d", "BLANK1", alpha, color, color_enable, alpha_highlight, scale_basis, operator = "dialog_operator", action = "light_color", arg = "Adjust color", operation = "Lumiere")

	def refresh(self, context):
		light = context.object

		color = 0.2,0.2,0.2
		color_enable = hex_to_rgb(0x9BBBE1)

		if light.Lumiere.select_only:
			self.select_only_2dwidget.color = color_enable
		else:
			self.select_only_2dwidget.color = color

	def draw_prepare(self, context):
		addon_prefs = get_preferences()
		light = context.object
		self.color_2dwidget.color = light.Lumiere.light_color[:3]
		self.color_2dwidget.color_highlight = light.Lumiere.light_color[:3]

		i = 2
		width = 35
		height = 40

		if addon_prefs.lights_2dgizmos == False or context.scene.is_running:
			self.energy_2dwidget.hide = True
			self.range_2dwidget.hide = True
			self.scale_2dwidget.hide = True
			self.scale_x_2dwidget.hide = True
			self.scale_y_2dwidget.hide = True
			self.rotation_2dwidget.hide = True
			self.spin_2dwidget.hide = True
			self.tilt_2dwidget.hide = True
			self.select_only_2dwidget.hide = True
			self.raycast_2dwidget.hide = True
			self.spot_size_2dwidget.hide = True
			self.spot_blend_2dwidget.hide = True
			self.light_type_2dwidget.hide = True
			self.color_2dwidget.hide = True

		else:

			#-- Energy
			self.energy_2dwidget.hide = False
			self.energy_2dwidget.matrix_basis[0][3] = width*i
			self.energy_2dwidget.matrix_basis[1][3] = height
			self.energy_2dwidget.use_draw_modal = True
			draw_highlight_gizmo(context, self.energy_2dwidget, "Energy", width*i)
			i += 1

			#-- Range
			self.range_2dwidget.hide = False
			self.range_2dwidget.matrix_basis[0][3] = width*i
			self.range_2dwidget.matrix_basis[1][3] = height
			self.range_2dwidget.use_draw_modal = True
			draw_highlight_gizmo(context, self.range_2dwidget, "Range", width*i)
			i += 1

			#-- Scale
			self.scale_2dwidget.hide = False
			self.scale_2dwidget.matrix_basis[0][3] = width*i
			self.scale_2dwidget.matrix_basis[1][3] = height
			self.scale_2dwidget.use_draw_modal = True
			draw_highlight_gizmo(context, self.scale_2dwidget, "Scale", width*i)

			i += 1

			self.scale_x_2dwidget.hide = True
			self.scale_y_2dwidget.hide = True
			if light.type == 'MESH' or (light.type == 'LIGHT' and light.data.type == "AREA" and light.data.shape not in ('SQUARE', 'DISK')):
				#-- Scale X
				self.scale_x_2dwidget.hide = False
				self.scale_x_2dwidget.matrix_basis[0][3] = width*i
				self.scale_x_2dwidget.matrix_basis[1][3] = height
				self.scale_x_2dwidget.use_draw_modal = True
				draw_highlight_gizmo(context, self.scale_x_2dwidget, "Scale x", width*i)
				i += 1

				#-- Scale Y
				self.scale_y_2dwidget.hide = False
				self.scale_y_2dwidget.matrix_basis[0][3] = width*i
				self.scale_y_2dwidget.matrix_basis[1][3] = height
				self.scale_y_2dwidget.use_draw_modal = True
				draw_highlight_gizmo(context, self.scale_y_2dwidget, "Scale y", width*i)
				i += 1

			#-- Rotation
			self.rotation_2dwidget.hide = False
			self.rotation_2dwidget.matrix_basis[0][3] = width*i
			self.rotation_2dwidget.matrix_basis[1][3] = height
			self.rotation_2dwidget.use_draw_modal = True
			draw_highlight_gizmo(context, self.rotation_2dwidget, "Rotate", width*i)
			i += 1

			#-- Spin
			self.spin_2dwidget.hide = False
			self.spin_2dwidget.matrix_basis[0][3] = width*i
			self.spin_2dwidget.matrix_basis[1][3] = height
			self.spin_2dwidget.use_draw_modal = True
			draw_highlight_gizmo(context, self.spin_2dwidget, "Spin", width*i)
			i += 1

			#-- Tilt
			self.tilt_2dwidget.hide = False
			self.tilt_2dwidget.matrix_basis[0][3] = width*i
			self.tilt_2dwidget.matrix_basis[1][3] = height
			self.tilt_2dwidget.use_draw_modal = True
			draw_highlight_gizmo(context, self.tilt_2dwidget, "Tilt", width*i)
			i += 1

			#-- Spot: Cone size / Cone blend
			self.spot_size_2dwidget.hide = True
			self.spot_blend_2dwidget.hide = True
			if light.type == 'LIGHT' and light.data.type == 'SPOT':
				self.spot_size_2dwidget.hide = False
				self.spot_size_2dwidget.matrix_basis[0][3] = width*i
				self.spot_size_2dwidget.matrix_basis[1][3] = height
				self.spot_size_2dwidget.use_draw_modal = True
				draw_highlight_gizmo(context, self.spot_size_2dwidget, "Spot size", width*i)
				i += 1

				self.spot_blend_2dwidget.hide = False
				self.spot_blend_2dwidget.matrix_basis[0][3] = width*i
				self.spot_blend_2dwidget.matrix_basis[1][3] = height
				self.spot_blend_2dwidget.use_draw_modal = True
				draw_highlight_gizmo(context, self.spot_blend_2dwidget, "Spot blend", width*i)
				i += 1

			#-- Select only
			self.select_only_2dwidget.hide = False
			self.select_only_2dwidget.matrix_basis[0][3] = width*i
			self.select_only_2dwidget.matrix_basis[1][3] = height
			self.select_only_2dwidget.use_draw_modal = True
			draw_highlight_gizmo(context, self.select_only_2dwidget, "Show only", width*i)
			i += 1

			#-- Raycast
			self.raycast_2dwidget.hide = False
			self.raycast_2dwidget.matrix_basis[0][3] = width*i
			self.raycast_2dwidget.matrix_basis[1][3] = height
			self.raycast_2dwidget.use_draw_modal = True
			draw_highlight_gizmo(context, self.raycast_2dwidget, "Modal", width*i)
			i += 1

			#-- Light type
			self.light_type_2dwidget.hide = False
			self.light_type_2dwidget.matrix_basis[0][3] = width*i
			self.light_type_2dwidget.matrix_basis[1][3] = height
			self.light_type_2dwidget.use_draw_modal = True
			draw_highlight_gizmo(context, self.light_type_2dwidget, "Light type", width*i)
			i += 1

			#-- Light type
			self.color_2dwidget.hide = False
			self.color_2dwidget.matrix_basis[0][3] = width*i
			self.color_2dwidget.matrix_basis[1][3] = height
			self.color_2dwidget.use_draw_modal = True
			draw_highlight_gizmo(context, self.color_2dwidget, "Color", width*i)
			i += 1

# -------------------------------------------------------------------- #
# LIGHTS 3D Gizmos
class LUMIERE_GGT_3dgizmo(GizmoGroup):
	bl_idname = "LUMIERE_GGT_3dgizmo"
	bl_label = "Lumiere widget"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'WINDOW'
	bl_options = {'3D', 'PERSISTENT', 'SHOW_MODAL_ALL'}

	@classmethod
	def poll(cls, context):
		light = context.object
		primary_col, light_col, platform_col = get_collection()
		if context.active_object:
			#and light_col is not None and len(light_col.objects) > 0 :
			if light_col and len(light_col.objects) > 0 :
				return context.view_layer.objects.active.name in light_col.all_objects and light.mode == 'OBJECT'
		else:
			return False


	def setup(self, context):
		light = context.object

		color_select = context.preferences.themes['Default'].view_3d.bone_pose_active
		color_active = context.preferences.themes['Default'].view_3d.bone_pose
		scale_basis = 0.07
		color_alpha = 0.8
		alpha_highlight = 1
		color_highlight = 0.8
		line_width = 5
		line_length = .4

		#-- HIT Gizmo
		gz_hit = self.gizmos.new("GIZMO_GT_move_3d")
		op = gz_hit.target_set_operator("lumiere.ray_operator")
		op.arg = "Interactive lighting"
		op.operation = "ray_cast"
		gz_hit.draw_options={"FILL", "ALIGN_VIEW"}
		gz_hit.scale_basis = scale_basis
		gz_hit.color = color_active
		gz_hit.alpha = color_alpha
		gz_hit.color_highlight = color_select
		gz_hit.alpha_highlight = alpha_highlight
		gz_hit.line_width = 3
		gz_hit.use_select_background = True
		self.hit_widget = gz_hit

		#-- RANGE Gizmo
		gz_range = self.gizmos.new("GIZMO_GT_arrow_3d")
		gz_range.draw_style = 'BOX' #('NORMAL', 'CROSS', 'BOX', 'CONE')
		gz_range.scale_basis = .8
		gz_range.color = color_active
		gz_range.alpha = color_alpha
		gz_range.color_highlight = color_select
		gz_range.alpha_highlight = alpha_highlight
		gz_range.line_width = 0
		gz_range.length  = 0
		self.range_widget = gz_range

		#-- SCALE_XY / SCALE_Y Gizmo
		gz_scale = self.gizmos.new("GIZMO_GT_arrow_3d")
		gz_scale.draw_style = 'BOX' #('NORMAL', 'CROSS', 'BOX', 'CONE')
		gz_scale.scale_basis = 0.15
		gz_scale.color =  color_active
		gz_scale.alpha = color_alpha
		gz_scale.color_highlight = color_select
		gz_scale.alpha_highlight = alpha_highlight
		gz_scale.line_width = line_width
		self.scale_xy_widget = gz_scale

		#-- SCALE_X Gizmo
		gz_scale_x = self.gizmos.new("GIZMO_GT_arrow_3d")
		gz_scale_x.draw_style = 'BOX' #('NORMAL', 'CROSS', 'BOX', 'CONE')
		gz_scale_x.scale_basis = 0.15
		gz_scale_x.color =  color_active
		gz_scale_x.alpha = color_alpha
		gz_scale_x.color_highlight = color_select
		gz_scale_x.alpha_highlight = alpha_highlight
		gz_scale_x.line_width = line_width
		self.scale_x_widget = gz_scale_x

		#-- Shadow Gizmo
		gz_shadow = self.gizmos.new("GIZMO_GT_move_3d")
		op_shadow = gz_shadow.target_set_operator("lumiere.ray_operator")
		op_shadow.action = "shadow"
		op_shadow.arg = "Shadow helper"
		gz_shadow.draw_options={"ALIGN_VIEW"}
		gz_shadow.color = color_active
		gz_shadow.alpha = color_alpha
		gz_shadow.color_highlight = color_select
		gz_shadow.alpha_highlight = alpha_highlight
		gz_shadow.scale_basis = scale_basis*.8
		self.gz_shadow_widget = gz_shadow

		#-- BBOX Gizmo
		bbox_circle = self.gizmos.new("GIZMO_GT_move_3d")
		bbox_circle.draw_options={"FILL", "ALIGN_VIEW"}
		bbox_circle.scale_basis = scale_basis
		bbox_circle.alpha = color_alpha
		bbox_circle.hide_select = True
		self.bbox_circle_widget = bbox_circle

		gz_bbox_x = self.gizmos.new("GIZMO_GT_arrow_3d")
		gz_bbox_x.color  = context.preferences.themes[0].user_interface.axis_x
		gz_bbox_x.length  = line_length
		gz_bbox_x.alpha = color_alpha
		gz_bbox_x.scale_basis = 0.8
		self.bbox_x_widget = gz_bbox_x

		gz_bbox_y = self.gizmos.new("GIZMO_GT_arrow_3d")
		gz_bbox_y.color  = context.preferences.themes[0].user_interface.axis_y
		gz_bbox_y.length  = line_length
		gz_bbox_y.alpha = color_alpha
		gz_bbox_y.scale_basis = 0.8
		self.bbox_y_widget = gz_bbox_y

		gz_bbox_z = self.gizmos.new("GIZMO_GT_arrow_3d")
		gz_bbox_z.color  = context.preferences.themes[0].user_interface.axis_z
		gz_bbox_z.length  = line_length
		gz_bbox_z.alpha = color_alpha
		gz_bbox_z.scale_basis = 0.8
		self.bbox_z_widget = gz_bbox_z

		#-- SPOT CONE Gizmo
		# spot_circle = self.gizmos.new("GIZMO_GT_dial_3d")
		# spot_circle.draw_options={"ANGLE_VALUE"}
		spot_circle = self.gizmos.new("GIZMO_GT_move_3d")
		op = spot_circle.target_set_operator("lumiere.light_spot")
		op.arg = "Spot size"
		# spot_circle.draw_options={"ALIGN_VIEW"}
		spot_circle.draw_style = 'RING_2D' #('RING_2D', 'CROSS_2D')
		spot_circle.scale_basis = .4
		spot_circle.color = color_active
		spot_circle.alpha = color_alpha
		spot_circle.color_highlight = color_select
		spot_circle.alpha_highlight = alpha_highlight
		spot_circle.line_width = 2
		self.spot_circle_widget = spot_circle

# -------------------------------------------------------------------- #
	def draw_prepare(self, context):
		addon_prefs = get_preferences()

		light = context.active_object
		region = context.region
		mat_hit = Matrix.Translation((light.Lumiere.hit))
		mat_shadow = Matrix.Translation((light.Lumiere.shadow))
		mat_rot = light.rotation_euler.to_matrix()
		hit_matrix = mat_hit @ mat_rot.to_4x4()
		mat_rot_x = Matrix.Rotation(radians(90.0), 4, 'Y')
		mat_rot_y = Matrix.Rotation(radians(90.0), 4, 'X')

		# Check preferences and if operator is running
		if addon_prefs.lights_3dgizmos == False or context.scene.is_running:
			self.hit_widget.hide = True
			self.range_widget.hide = True
			self.scale_xy_widget.hide = True
			self.scale_x_widget.hide = True
			self.gz_shadow_widget.hide = True
			self.bbox_circle_widget.hide = True
			self.bbox_x_widget.hide = True
			self.bbox_y_widget.hide = True
			self.bbox_z_widget.hide = True
			self.spot_circle_widget.hide = True
		else:

			# Hide spot widget
			self.spot_circle_widget.hide = True

			# Scale X
			def get_x_widget():
				light = bpy.context.object
				value = light.Lumiere.scale_x * light.Lumiere.scale_xy
				return value

			def set_x_widget(value):
				self.test_prop = "scale_x"
				light = bpy.context.object
				light.Lumiere.scale_x = value / light.Lumiere.scale_xy

			# Scale Y
			def get_y_widget():
				light = bpy.context.object
				value = light.Lumiere.scale_y * light.Lumiere.scale_xy
				return value

			def set_y_widget(value):
				self.test_prop = "scale_y"
				light = bpy.context.object
				if light.Lumiere.lock_scale:
					light.Lumiere.scale_xy = value / light.Lumiere.scale_y
				else:
					light.Lumiere.scale_y = value / light.Lumiere.scale_xy

			# Scale X and Y only for Softbox and Area
			if light.type == 'MESH' or (light.type == 'LIGHT' and light.data.type == "AREA" and light.data.shape not in ('SQUARE', 'DISK')):

				self.scale_xy_widget.hide = False

				if light.Lumiere.lock_scale:
					self.scale_x_widget.hide = True
					self.scale_xy_widget.target_set_prop('offset', light.Lumiere, 'scale_xy')
					self.scale_xy_widget.target_set_handler('offset', get=get_y_widget, set=set_y_widget)
				else:
					self.scale_x_widget.hide = False
					self.scale_x_widget.target_set_prop('offset', light.Lumiere, 'scale_x')
					self.scale_x_widget.target_set_handler('offset', get=get_x_widget, set=set_x_widget)

					self.scale_xy_widget.target_set_prop('offset', light.Lumiere, 'scale_y')
					self.scale_xy_widget.target_set_handler('offset', get=get_y_widget, set=set_y_widget)

			elif light.type == 'LIGHT' and light.data.type == "SPOT":
				self.spot_circle_widget.hide = False
				self.spot_circle_widget.matrix_basis = hit_matrix.normalized()
				self.scale_xy_widget.hide = False
				self.scale_xy_widget.target_set_handler('offset', get=get_y_widget, set=set_y_widget)
			else:
				self.scale_x_widget.hide = True
				self.scale_xy_widget.hide = False
				self.scale_xy_widget.target_set_handler('offset', get=get_y_widget, set=set_y_widget)

			# Hit
			self.hit_widget.hide = False
			self.hit_widget.matrix_basis = hit_matrix.normalized()

			# Range
			self.range_widget.hide = False
			self.range_widget.target_set_prop('offset', light.Lumiere, 'range')
			self.range_widget.matrix_basis = light.matrix_world.normalized() @ Matrix.Translation((0, 0, -self.range_widget.target_get_value("offset")))

			# Shadow gizmo : Hide if at center or link to the environment
			if light.Lumiere.shadow[:] != (0,0,0) and not light.Lumiere.lock_img:
				self.gz_shadow_widget.hide = False
				self.gz_shadow_widget.matrix_basis = mat_shadow.normalized()
			else:
				self.gz_shadow_widget.hide = True

			self.scale_xy_widget.matrix_basis = light.matrix_world.normalized() @ mat_rot_y
			self.scale_x_widget.matrix_basis = light.matrix_world.normalized() @ mat_rot_x

			# Estimated Bounding Box widget
			if light.Lumiere.reflect_angle == "Estimated" and not light.Lumiere.auto_bbox_center:
				mat_bbox = Matrix.Translation((light.Lumiere.bbox_center))
				mat_bbox_x = Matrix.Rotation(radians(90.0), 4, 'Y')
				mat_bbox_y = Matrix.Rotation(radians(-90.0), 4, 'X')

				self.bbox_circle_widget.hide = False
				self.bbox_x_widget.hide = False
				self.bbox_y_widget.hide = False
				self.bbox_z_widget.hide = False

				def get_bbox_x():
					light = bpy.context.object
					return light.Lumiere.bbox_center[0]

				def set_bbox_x(bbox_x):
					light = bpy.context.object
					global_bbox_center = light.Lumiere.bbox_center
					global_bbox_center[0] = bbox_x

				def get_bbox_y():
					light = bpy.context.object
					return light.Lumiere.bbox_center[1]

				def set_bbox_y(bbox_y):
					light = bpy.context.object
					global_bbox_center = light.Lumiere.bbox_center
					global_bbox_center[1] = bbox_y

				def get_bbox_z():
					light = bpy.context.object
					return light.Lumiere.bbox_center[2]

				def set_bbox_z(bbox_z):
					light = bpy.context.object
					global_bbox_center = light.Lumiere.bbox_center
					global_bbox_center[2] = bbox_z

				self.bbox_circle_widget.matrix_basis = mat_bbox.normalized()

				self.bbox_x_widget.target_set_handler('offset', get=get_bbox_x, set=set_bbox_x)
				self.bbox_x_widget.matrix_basis = mat_bbox.normalized() @ mat_bbox_x
				self.bbox_x_widget.matrix_basis.col[3][0] = light.Lumiere.bbox_center[0] - self.bbox_x_widget.target_get_value("offset")[0]

				self.bbox_y_widget.target_set_handler('offset', get=get_bbox_y, set=set_bbox_y)
				self.bbox_y_widget.matrix_basis = mat_bbox.normalized() @ mat_bbox_y
				self.bbox_y_widget.matrix_basis.col[3][1] = light.Lumiere.bbox_center[1] - self.bbox_y_widget.target_get_value("offset")[0]

				self.bbox_z_widget.target_set_handler('offset', get=get_bbox_z, set=set_bbox_z)
				self.bbox_z_widget.matrix_basis = mat_bbox.normalized()
				self.bbox_z_widget.matrix_basis.col[3][2] = light.Lumiere.bbox_center[2] - self.bbox_z_widget.target_get_value("offset")[0]
			else:
				self.bbox_circle_widget.hide = True
				self.bbox_x_widget.hide = True
				self.bbox_y_widget.hide = True
				self.bbox_z_widget.hide = True

# -------------------------------------------------------------------- #
# UTILS
# https://blender.stackexchange.com/questions/158896/how-set-hex-in-rgb-node-python
def srgb_to_linearrgb(c):
	if   c < 0:       return 0
	elif c < 0.04045: return c/12.92
	else:             return ((c+0.055)/1.055)**2.4

def hex_to_rgb(h,alpha=1):
	r = (h & 0xff0000) >> 16
	g = (h & 0x00ff00) >> 8
	b = (h & 0x0000ff)
	return tuple([srgb_to_linearrgb(c/0xff) for c in (r,g,b)])

# Register
# -------------------------------------------------------------------- #

classes = [
	LUMIERE_GGT_3dgizmo,
	LUMIERE_OT_2dgizmo_light,
	LUMIERE_GGT_2dgizmo_light,
	]

def register():
	from bpy.utils import register_class
	for cls in classes:
		register_class(cls)


def unregister():
	from bpy.utils import unregister_class
	for cls in reversed(classes):
		unregister_class(cls)
