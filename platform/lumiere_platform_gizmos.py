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
# PLATFORM 2D Gizmos
class LUMIERE_OT_2dgizmo_platform(Operator):
	bl_idname = "lumiere.2dgizmo_platform"
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

		platform = context.object
		if event.type == 'LEFTMOUSE':

			# None modal action
			if self.action == "shade_smooth":
				platform.Lumiere_platform.shade_smooth = not platform.Lumiere_platform.shade_smooth
			else:
				self.init_value = self.save_value = getattr(platform.Lumiere_platform, self.action)

				bpy.types.STATUSBAR_HT_header.draw = status_bar_draw
				context.window_manager.modal_handler_add(self)
				self.draw_handle_2d = bpy.types.SpaceView3D.draw_handler_add(draw_gizmo_2d_label, (self, context, self.action, "platform"), "WINDOW", "POST_PIXEL")

				return {"RUNNING_MODAL"}

		return {'FINISHED'}

	def modal(self, context, event):
		platform = context.object
		shift_press = event.shift and event.value == 'PRESS'
		accuracy = 200 if shift_press else 50

		if "MOUSEMOVE" in event.type :
			delta_x = (event.mouse_x - self.init_mouse_x) / accuracy
			setattr(platform.Lumiere_platform, self.action, self.init_value + delta_x)

			return {"RUNNING_MODAL"}

		elif event.type == "RIGHTMOUSE":
			setattr(platform.Lumiere_platform, self.action, self.save_value)
			if self.draw_handle_2d is not None:
				self.unregister_handlers(context)
			return {'CANCELLED'}

		elif "SHIFT" in event.type :
			return {'PASS_THROUGH'}

		if self.draw_handle_2d is not None:
			self.unregister_handlers(context)
		return {'FINISHED'}

# -------------------------------------------------------------------- #
class LUMIERE_GGT_2dgizmo_platform(GizmoGroup):
	bl_idname = "LUMIERE_GGT_2dgizmo_platform"
	bl_label = "Lumiere platform 2dwidget"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'WINDOW'
	bl_options = {'PERSISTENT', 'SCALE'}

	@classmethod
	def poll(cls, context):
		platform = context.object
		primary_col, light_col, platform_col = get_collection()
		if context.active_object:
			if platform_col and len(platform_col.objects) > 0 :
				return context.view_layer.objects.active.name in platform_col.all_objects and platform.mode == 'OBJECT'
		else:
			return False

	def __init__(self):
		self.platform_color = (0,0,0)
# -------------------------------------------------------------------- #
	def setup(self, context):
		platform = context.object
		color_menu = hex_to_rgb(0xE7CFBC)
		color_enable = hex_to_rgb(0x9BBBE1)
		# color_alpha = (0,0,0,1)
		color_highlight = 0.5,0.5,0.5#0.8, 0.8, 0.8
		alpha = .8
		color = 0.2,0.2,0.2
		alpha_highlight = 1#0.2
		scale_basis = (80 * 0.35) / 2

		#-- Shade smooth
		self.shade_smooth_2dwidget = create_2d_gizmo(self, context, "GIZMO_GT_button_2d", "MOD_SMOOTH", alpha, color, color_enable, alpha_highlight, scale_basis, operator = "2dgizmo_platform", action = "shade_smooth", arg = "Enable shade smooth")

		#-- Platform type
		self.platform_type_2dwidget = create_2d_gizmo(self, context, "GIZMO_GT_button_2d", "OUTLINER_OB_SURFACE", alpha, color, color_menu, alpha_highlight, scale_basis, operator = "dialog_operator", action = "platform_type", arg = "Select platform type", operation = "Lumiere_platform")

		#-- Bevel segments
		self.bevel_segment_2dwidget = create_2d_gizmo(self, context, "GIZMO_GT_button_2d", "MOD_BEVEL", alpha, color, color_highlight, alpha_highlight, scale_basis, operator = "2dgizmo_platform", action = "bevel_segment", arg = "Adjust bevel segments")

		#-- Bevel offset
		self.bevel_offset_2dwidget = create_2d_gizmo(self, context, "GIZMO_GT_button_2d", "DRIVER_ROTATIONAL_DIFFERENCE", alpha, color, color_highlight, alpha_highlight, scale_basis, operator = "2dgizmo_platform", action = "bevel_offset", arg = "Adjust bevel offset")

		#-- Height
		self.height_2dwidget = create_2d_gizmo(self, context, "GIZMO_GT_button_2d", "FILE_PARENT", alpha, color, color_highlight, alpha_highlight, scale_basis, operator = "2dgizmo_platform", action = "height", arg = "Adjust height")

		#-- Scale X
		self.scale_x_2dwidget = create_2d_gizmo(self, context, "GIZMO_GT_button_2d", "SORT_DESC", alpha, color, color_highlight, alpha_highlight, scale_basis, operator = "2dgizmo_platform", action = "scale_x", arg = "Scale X")

		#-- Scale Y
		self.scale_y_2dwidget = create_2d_gizmo(self, context, "GIZMO_GT_button_2d", "FORWARD", alpha, color, color_highlight, alpha_highlight, scale_basis, operator = "2dgizmo_platform", action = "scale_y", arg = "Scale Y")

		#-- Ceiling
		self.ceiling_2dwidget = create_2d_gizmo(self, context, "GIZMO_GT_button_2d", "LOOP_FORWARDS", alpha, color, color_highlight, alpha_highlight, scale_basis, operator = "2dgizmo_platform", action = "ceiling", arg = "Adjust ceiling")

		#-- Scale
		self.scale_2dwidget = create_2d_gizmo(self, context, "GIZMO_GT_button_2d", "FULLSCREEN_ENTER", alpha, color, color_highlight, alpha_highlight, scale_basis, operator = "2dgizmo_platform", action = "scale", arg = "Adjust scale")

		#-- Color
		self.color_2dwidget = create_2d_gizmo(self, context, "GIZMO_GT_button_2d", "BLANK1", 1, color, color_highlight, 1, scale_basis, operator = "dialog_operator", action = "platform_color", arg = "Adjust color", operation = "Lumiere_platform")

	def refresh(self, context):
		platform = context.object
		color = 0.2,0.2,0.2
		color_enable = hex_to_rgb(0x9BBBE1)
		if platform.Lumiere_platform.shade_smooth:
			self.shade_smooth_2dwidget.color = color_enable
		else:
			self.shade_smooth_2dwidget.color = color


	def draw_prepare(self, context):
		addon_prefs = get_preferences()

		platform = context.object
		self.color_2dwidget.color = platform.Lumiere_platform.platform_color[:3]
		self.color_2dwidget.color_highlight = platform.Lumiere_platform.platform_color[:3]
		region = context.region
		i = 2
		width = 35
		height = 40

		if addon_prefs.platform_2dgizmos == False:
			self.shade_smooth_2dwidget.hide = True
			self.bevel_segment_2dwidget.hide = True
			self.bevel_offset_2dwidget.hide = True
			self.height_2dwidget.hide = True
			self.scale_x_2dwidget.hide = True
			self.scale_y_2dwidget.hide = True
			self.scale_2dwidget.hide = True
			self.ceiling_2dwidget.hide = True
			self.platform_type_2dwidget.hide = True
			self.color_2dwidget.hide = True
		else:

			#-- Bevel offset
			self.bevel_offset_2dwidget.hide = False
			self.bevel_offset_2dwidget.matrix_basis[0][3] = width*i
			self.bevel_offset_2dwidget.matrix_basis[1][3] = height
			self.bevel_offset_2dwidget.use_draw_modal = True
			draw_highlight_gizmo(context, self.bevel_offset_2dwidget, "Bevel offset", width*i)
			i += 1

			#-- Bevel segments
			self.bevel_segment_2dwidget.hide = False
			self.bevel_segment_2dwidget.matrix_basis[0][3] = width*i
			self.bevel_segment_2dwidget.matrix_basis[1][3] = height
			self.bevel_segment_2dwidget.use_draw_modal = True
			draw_highlight_gizmo(context, self.bevel_segment_2dwidget, "Segments", width*i)
			i += 1

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

			#-- Height
			self.height_2dwidget.hide = True
			if platform.Lumiere_platform.platform_type != "Plan":
				self.height_2dwidget.hide = False
				self.height_2dwidget.matrix_basis[0][3] = width*i
				self.height_2dwidget.matrix_basis[1][3] = height
				self.height_2dwidget.use_draw_modal = True
				draw_highlight_gizmo(context, self.height_2dwidget, "Height", width*i)
				i += 1

			#-- Ceiling
			self.ceiling_2dwidget.hide = True
			if platform.Lumiere_platform.platform_type == "C_curve":
				self.ceiling_2dwidget.hide = False
				self.ceiling_2dwidget.matrix_basis[0][3] = width*i
				self.ceiling_2dwidget.matrix_basis[1][3] = height
				self.ceiling_2dwidget.use_draw_modal = True
				draw_highlight_gizmo(context, self.ceiling_2dwidget, "Ceiling", width*i)
				i += 1

			#-- Scale
			self.scale_2dwidget.hide = False
			self.scale_2dwidget.matrix_basis[0][3] = width*i
			self.scale_2dwidget.matrix_basis[1][3] = height
			self.scale_2dwidget.use_draw_modal = True
			draw_highlight_gizmo(context, self.scale_2dwidget, "Scale", width*i)
			i += 1

			#-- Shade smooth
			self.shade_smooth_2dwidget.hide = False
			self.shade_smooth_2dwidget.matrix_basis[0][3] = width*i
			self.shade_smooth_2dwidget.matrix_basis[1][3] = height
			self.shade_smooth_2dwidget.use_draw_modal = True
			draw_highlight_gizmo(context, self.shade_smooth_2dwidget, "Smooth", width*i)
			i += 1

			#-- Platform type
			self.platform_type_2dwidget.hide = False
			self.platform_type_2dwidget.matrix_basis[0][3] = width*i
			self.platform_type_2dwidget.matrix_basis[1][3] = height
			self.platform_type_2dwidget.use_draw_modal = True
			draw_highlight_gizmo(context, self.platform_type_2dwidget, "Type", width*i)
			i += 1

			#-- Platform type
			self.color_2dwidget.hide = False
			self.color_2dwidget.matrix_basis[0][3] = width*i
			self.color_2dwidget.matrix_basis[1][3] = height
			self.color_2dwidget.use_draw_modal = True
			draw_highlight_gizmo(context, self.color_2dwidget, "Color", width*i)
			i += 1

# -------------------------------------------------------------------- #
# PLATFORM 3D Gizmos
class LUMIERE_GGT_3dgizmo_platform(GizmoGroup):
	bl_idname = "LUMIERE_GGT_3dgizmo_platform"
	bl_label = "Lumiere widget"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'WINDOW'
	bl_options = {'3D', 'PERSISTENT'}

	@classmethod
	def poll(cls, context):
		platform = context.object
		primary_col, light_col, platform_col = get_collection()
		if context.active_object:
			if platform_col and len(platform_col.objects) > 0 :
				return context.view_layer.objects.active.name in platform_col.all_objects and platform.mode == 'OBJECT'
		else:
			return False

# -------------------------------------------------------------------- #

	def setup(self, context):
		platform = context.active_object
		scale_y = platform.Lumiere_platform.scale_y * platform.Lumiere_platform.scale
		scale_x = platform.Lumiere_platform.scale_x * platform.Lumiere_platform.scale
		color_select = context.preferences.themes['Default'].view_3d.bone_pose_active
		color_active = context.preferences.themes['Default'].view_3d.bone_pose
		scale_basis = 0.15
		color_alpha = 0.8
		alpha_highlight = 1
		line_width = 5
		line_length = .4

		#-- Scale Gizmo
		scale_platform = self.gizmos.new("GIZMO_GT_arrow_3d")
		scale_platform.draw_style = 'BOX' #('NORMAL', 'CROSS', 'BOX', 'CONE')
		scale_platform.scale_basis = scale_basis
		scale_platform.color =  color_active
		scale_platform.alpha = color_alpha
		scale_platform.color_highlight = color_select
		scale_platform.alpha_highlight = alpha_highlight
		scale_platform.line_width = line_width
		self.scale_platform_3dwidget = scale_platform

		#-- Scale X Gizmo
		scale_x_platform = self.gizmos.new("GIZMO_GT_arrow_3d")
		scale_x_platform.draw_style = 'BOX' #('NORMAL', 'CROSS', 'BOX', 'CONE')
		scale_x_platform.scale_basis = scale_basis
		scale_x_platform.color =  color_active
		scale_x_platform.alpha = color_alpha
		scale_x_platform.color_highlight = color_select
		scale_x_platform.alpha_highlight = alpha_highlight
		scale_x_platform.line_width = line_width
		self.scale_x_platform_3dwidget = scale_x_platform

		#-- Scale Y Gizmo
		scale_y_platform = self.gizmos.new("GIZMO_GT_arrow_3d")
		scale_y_platform.draw_style = 'BOX' #('NORMAL', 'CROSS', 'BOX', 'CONE')
		scale_y_platform.scale_basis = scale_basis
		scale_y_platform.color =  color_active
		scale_y_platform.alpha = color_alpha
		scale_y_platform.color_highlight = color_select
		scale_y_platform.alpha_highlight = alpha_highlight
		scale_y_platform.line_width = line_width
		self.scale_y_platform_3dwidget = scale_y_platform

		#-- Ceiling Gizmo
		ceiling_platform = self.gizmos.new("GIZMO_GT_arrow_3d")
		ceiling_platform.draw_style = 'BOX' #('NORMAL', 'CROSS', 'BOX', 'CONE')
		ceiling_platform.scale_basis = scale_basis
		ceiling_platform.color =  color_active
		ceiling_platform.alpha = color_alpha
		ceiling_platform.color_highlight = color_select
		ceiling_platform.alpha_highlight = alpha_highlight
		ceiling_platform.line_width = line_width
		self.ceiling_platform_3dwidget = ceiling_platform

		#-- Height Gizmo
		height_platform = self.gizmos.new("GIZMO_GT_arrow_3d")
		height_platform.draw_style = 'BOX' #('NORMAL', 'CROSS', 'BOX', 'CONE')
		height_platform.scale_basis = scale_basis
		height_platform.color =  color_active
		height_platform.alpha = color_alpha
		height_platform.color_highlight = color_select
		height_platform.alpha_highlight = alpha_highlight
		height_platform.line_width = line_width
		self.height_platform_3dwidget = height_platform

		#-- Bevel Gizmo
		bevel_platform = self.gizmos.new("GIZMO_GT_arrow_3d")
		bevel_platform.draw_style = 'BOX' #('NORMAL', 'CROSS', 'BOX', 'CONE')
		bevel_platform.draw_options={"STEM"}
		bevel_platform.length  = 0
		bevel_platform.scale_basis = .7
		bevel_platform.color = color_active
		bevel_platform.alpha = color_alpha
		bevel_platform.color_highlight = color_select
		bevel_platform.alpha_highlight = alpha_highlight
		bevel_platform.line_width = 0
		self.bevel_platform_3dwidget = bevel_platform

		#-- Segments Bevel Gizmo
		segment_platform = self.gizmos.new("GIZMO_GT_arrow_3d")
		segment_platform.draw_style = 'NORMAL' #('NORMAL', 'CROSS', 'BOX', 'CONE')
		segment_platform.draw_options={"STEM"}
		segment_platform.length = .3
		segment_platform.scale_basis = .7
		segment_platform.color = color_active
		segment_platform.alpha = color_alpha
		segment_platform.color_highlight = color_select
		segment_platform.alpha_highlight = alpha_highlight
		segment_platform.line_width = -1
		self.segment_platform_3dwidget = segment_platform

# -------------------------------------------------------------------- #
	def draw_prepare(self, context):
		addon_prefs = get_preferences()
		platform = context.active_object

		_, _, vector_scale = platform.matrix_world.decompose()

		region = context.region
		scale_y = platform.Lumiere_platform.scale_y * platform.Lumiere_platform.scale
		scale_x = platform.Lumiere_platform.scale_x * platform.Lumiere_platform.scale
		height = platform.Lumiere_platform.height * platform.Lumiere_platform.scale
		scale = platform.Lumiere_platform.scale
		mat_rot = platform.rotation_euler.to_matrix()
		mat_rot_90x = Matrix.Rotation(radians(90.0), 4, 'X')
		mat_rot_90y = Matrix.Rotation(radians(-90.0), 4, 'Y')
		mat_rot_90z = Matrix.Rotation(radians(90.0), 4, 'Z')
		mat_scale = Matrix.Diagonal(vector_scale).to_4x4()

		# Check preferences and if operator is running
		if addon_prefs.platform_3dgizmos == False or context.scene.is_running == True:
			self.scale_platform_3dwidget.hide = True
			self.scale_x_platform_3dwidget.hide = True
			self.scale_y_platform_3dwidget.hide = True
			self.ceiling_platform_3dwidget.hide = True
			self.height_platform_3dwidget.hide = True
			self.bevel_platform_3dwidget.hide = True
			self.segment_platform_3dwidget.hide = True

		else:
			scale = platform.scale
			platform_matrix = Matrix.Translation((platform.location.x, platform.location.y, platform.location.z)) @ mat_rot.to_4x4()

			for area in bpy.context.screen.areas:
				if area.type == 'VIEW_3D':
					rv3d = area.spaces[0].region_3d
					if rv3d is not None:
						zoom = rv3d.view_distance

			# Scale X/Y
			self.scale_platform_3dwidget.hide = False
			self.scale_platform_3dwidget.target_set_prop('offset', platform.Lumiere_platform, 'scale')
			offset = self.scale_platform_3dwidget.target_get_value("offset")
			length_offset = sqrt((scale_x ** 2) + (scale_y ** 2))
			angle = degrees(atan(scale_x/scale_y))

			if platform.Lumiere_platform.platform_type == "Corner":
				scale_mat = platform_matrix  @ Matrix.Rotation(radians(-45.0), 4, 'Z') @ Matrix.Rotation(radians(90),4,'X') @ Matrix.Rotation(radians(angle), 4, 'Y') @ Matrix.Translation((0,0,length_offset-offset))
			else:
				scale_mat = platform_matrix @ Matrix.Rotation(radians(90),4,'X') @ Matrix.Rotation(radians(-angle), 4, 'Y') @ Matrix.Translation((0,0,length_offset-offset))

			self.scale_platform_3dwidget.matrix_basis = scale_mat.normalized()

			# Scale X
			def get_scale_x():
				platform = context.object
				offset = platform.Lumiere_platform.scale_x * platform.Lumiere_platform.scale * vector_scale[0]
				return offset

			def set_scale_x(offset):
				platform = context.object
				platform.Lumiere_platform.scale_x = offset / platform.Lumiere_platform.scale / vector_scale[0]

			self.scale_x_platform_3dwidget.hide = False
			self.scale_x_platform_3dwidget.target_set_prop('offset', platform.Lumiere_platform, 'scale_x')
			if platform.Lumiere_platform.platform_type == "Corner":
				scale_x_mat = platform_matrix @ Matrix.Rotation(radians(135.0), 4, 'Z')
			else:
				scale_x_mat = platform_matrix
			self.scale_x_platform_3dwidget.target_set_handler('offset', get=get_scale_x, set=set_scale_x)
			self.scale_x_platform_3dwidget.matrix_basis = scale_x_mat.normalized() @ mat_rot_90y

			# Scale Y
			def get_scale_y():
				platform = context.object
				offset = platform.Lumiere_platform.scale_y * platform.Lumiere_platform.scale * vector_scale[1]
				return offset

			def set_scale_y(offset):
				platform = context.object
				platform.Lumiere_platform.scale_y = offset / platform.Lumiere_platform.scale / vector_scale[1]

			self.scale_y_platform_3dwidget.hide = False
			self.scale_y_platform_3dwidget.target_set_prop('offset', platform.Lumiere_platform, 'scale_y')
			if platform.Lumiere_platform.platform_type == "Corner":
				scale_y_mat = platform_matrix @ Matrix.Rotation(radians(-45.0), 4, 'Z')
			else:
				scale_y_mat = platform_matrix
			self.scale_y_platform_3dwidget.target_set_handler('offset', get=get_scale_y, set=set_scale_y)
			self.scale_y_platform_3dwidget.matrix_basis = scale_y_mat.normalized() @ mat_rot_90x

			# Ceiling
			if platform.Lumiere_platform.platform_type == "C_curve":
				def get_ceiling():
					platform = context.object
					offset = platform.Lumiere_platform.ceiling * platform.Lumiere_platform.scale
					return offset

				def set_ceiling(offset):
					platform = context.object
					platform.Lumiere_platform.ceiling = offset / platform.Lumiere_platform.scale

				self.ceiling_platform_3dwidget.hide = False
				self.ceiling_platform_3dwidget.target_set_prop('offset', platform.Lumiere_platform, 'ceiling')
				offset = self.ceiling_platform_3dwidget.target_get_value("offset")
				ceiling_mat = platform_matrix @ Matrix.Translation((0, scale_y, height))

				self.ceiling_platform_3dwidget.target_set_handler('offset', get=get_ceiling, set=set_ceiling)
				self.ceiling_platform_3dwidget.matrix_basis = ceiling_mat.normalized() @ mat_rot_90x
			else:
				self.ceiling_platform_3dwidget.hide = True

			# Height
			if platform.Lumiere_platform.platform_type != "Plan":
				def get_height():
					platform = context.object
					offset = platform.Lumiere_platform.height * platform.Lumiere_platform.scale * vector_scale[2]
					return offset

				def set_height(offset):
					platform = context.object
					platform.Lumiere_platform.height = offset / platform.Lumiere_platform.scale / vector_scale[2]

				self.height_platform_3dwidget.hide = False
				self.height_platform_3dwidget.target_set_prop('offset', platform.Lumiere_platform, 'height')
				if platform.Lumiere_platform.platform_type == "Corner":
					height_mat = platform_matrix @ Matrix.Rotation(radians(-45.0), 4, 'Z') @ Matrix.Translation((-scale_x,scale_y,0))
				else:
					height_mat = platform_matrix @ mat_scale @ Matrix.Translation((0, scale_y, 0))
				self.height_platform_3dwidget.target_set_handler('offset', get=get_height, set=set_height)

				self.height_platform_3dwidget.matrix_basis = height_mat.normalized()
			else:
				self.height_platform_3dwidget.hide = True

			# Bevel
			self.bevel_platform_3dwidget.hide = False
			if platform.Lumiere_platform.platform_type == "Corner":
				bevel_mat = platform_matrix @ Matrix.Rotation(radians(45.0), 4, 'Z') @ Matrix.Translation((scale_y,scale_x,0))
			else:
				bevel_mat = platform_matrix @ Matrix.Translation((scale_x, scale_y, 0))

			self.bevel_platform_3dwidget.target_set_prop('offset', platform.Lumiere_platform, 'bevel_offset')
			self.bevel_platform_3dwidget.matrix_basis = bevel_mat.normalized() @  mat_rot_90x

			# Segments
			def get_segment_x():
			    platform = context.object
			    offset = float(platform.Lumiere_platform.bevel_segment/(50/zoom))
			    return offset

			def set_segment_x(offset):
			    platform = context.object
			    platform.Lumiere_platform.bevel_segment = int(offset*(50/zoom))

			self.segment_platform_3dwidget.hide = False
			bevel_offset = self.bevel_platform_3dwidget.target_get_value('offset')
			self.segment_platform_3dwidget.target_set_prop('offset', platform.Lumiere_platform, 'bevel_segment')
			self.segment_platform_3dwidget.target_set_handler('offset', get=get_segment_x, set=set_segment_x)
			offset = self.segment_platform_3dwidget.target_get_value("offset")[0]

			if platform.Lumiere_platform.platform_type == "Corner":
			    segment_mat = platform_matrix @ Matrix.Rotation(radians(45.0), 4, 'Z') @ Matrix.Translation((scale_y, scale_x - bevel_offset, -offset+.15))
			else:
			    segment_mat = platform_matrix @ Matrix.Translation((scale_x - .02, scale_y - bevel_offset, -offset))

			self.segment_platform_3dwidget.matrix_basis = segment_mat.normalized()


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
#

classes = [
	LUMIERE_GGT_3dgizmo_platform,
	LUMIERE_GGT_2dgizmo_platform,
	LUMIERE_OT_2dgizmo_platform,
	]

def register():
	from bpy.utils import register_class
	for cls in classes:
		register_class(cls)

def unregister():
	from bpy.utils import unregister_class
	for cls in reversed(classes):
		unregister_class(cls)
