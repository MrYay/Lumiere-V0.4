import bpy
import blf
import bgl
import sys
import gpu
from gpu_extras.batch import batch_for_shader

from bpy_extras import view3d_utils
from mathutils import Vector
from mathutils.geometry import intersect_line_plane
from bpy_extras.view3d_utils import (
	region_2d_to_vector_3d,
	region_2d_to_location_3d,
	location_3d_to_region_2d,
)

from math import (
	degrees,
	sqrt,
	)

from .lumiere_utils import (
	draw_circle,
	create_2d_circle,
	)

# -------------------------------------------------------------------- #
def draw_highlight_gizmo(context, gizmo, text, position):
	"""
	Draw text to indicate the highlighted gizmo
	text : Text to draw.
	position : Position of the gizmo.
	round : Round the float to an int.
	"""
	if gizmo.is_highlight:
		context.object.select_set(True)

		region = context.region
		blf.size(0, 24, 45)
		blf.shadow(0, 3, 0, 0, 0, 1)
		blf.shadow_offset(0,0,0)
		blf.enable(0,blf.SHADOW)
		blf.position(0, position - blf.dimensions(0, text)[0] / 2, 60 , 0)
		blf.draw(0, text)
		blf.disable(0,blf.SHADOW)

# -------------------------------------------------------------------- #
def draw_gizmo_2d_label(self, context, action, origin):
	"""
	Draw text to indicate the current gizmo value.
	action : Gizmo type.
	origin : Gizmo from a light or a platform.
	"""
	region = context.region
	rv3d = context.region_data
	width = 35
	height = 40
	if origin == "light":
		active_obj = context.active_object.Lumiere
	elif origin == "platform":
		active_obj = context.active_object.Lumiere_platform

	if action == "spin":
		text = str(round(degrees(getattr(active_obj, action)), 2))
	elif action in ("spot_size", "spot_blend"):
		text = str(round(degrees(getattr(context.active_object.data, action)), 2))
	elif action == "bevel_segment":
		text = str(int(getattr(active_obj, action)))
	else:
		text = str(round(getattr(active_obj, action), 2))

	xt = int(region.width / 2.0)
	blf.size(0, 24, 72)
	blf.shadow(0, 3, 0, 0, 0, 1)
	blf.shadow_offset(0,0,0)
	blf.enable(0,blf.SHADOW)
	blf.position(0, xt - blf.dimensions(0, text)[0] / 2, 5 , 0)
	blf.draw(0, text)
	blf.disable(0,blf.SHADOW)

# -------------------------------------------------------------------- #
def draw_callback_lumiere(self, context):
	"""
	Draw '-Lumiere-' to indicate that the modal is running.
	"""

	region = context.region
	if context.area == self.lumiere_area:

		# Draw text to indicate that Lumiere is active
		text = "- Lumiere -"
		xt = int(region.width / 2.0)
		blf.size(0, 24, 72)
		blf.shadow(0, 3, 0, 0, 0, 1)
		blf.shadow_offset(0,0,0)
		blf.enable(0,blf.SHADOW)
		blf.position(0, xt - blf.dimensions(0, text)[0] / 2, 40 , 0)
		blf.draw(0, text)
		blf.disable(0,blf.SHADOW)

# -------------------------------------------------------------------- #
def draw_callback_2d(self, context):
	"""
	Draw 2d circles indicator.
	"""

	region = context.region
	rv3d = context.region_data

	# Draw text to indicate that Lumiere is active
	draw_callback_lumiere(self, context)

	if self.light:
		# Create a circle using a tri fan
		light = self.light
		color = context.preferences.themes[0].view_3d.object_active
		circle_hit = location_3d_to_region_2d(region, rv3d, light.Lumiere.hit)
		circle_radius = (circle_hit[0] + 4, circle_hit[1] + 4)
		steps = 8

		tris_coords, indices = draw_circle(circle_hit, circle_radius, steps)
		draw_shader(self, color, 1.0, 'TRI_FAN', tris_coords, size=1)

		if self.shadow:
			circle_hit = location_3d_to_region_2d(region, rv3d, light.Lumiere.shadow)
			circle_radius = (circle_hit[0] + 3, circle_hit[1] + 3)
			tris_coords, indices = draw_circle(circle_hit, circle_radius, steps)
			draw_shader(self, color, 1.0, 'TRI_FAN', tris_coords, size=1)

		# Draw circle on boundingbox center of the targeted object
		elif light.Lumiere.reflect_angle == "Estimated" and light.parent:
				circle_hit = location_3d_to_region_2d(region, rv3d, light.Lumiere.bbox_center)
				circle_radius = (circle_hit[0] + 3, circle_hit[1] + 3)
				steps = 8
				tris_coords, indices = draw_circle(circle_hit, circle_radius, steps)
				draw_shader(self, color, 1, 'TRI_FAN', tris_coords, size=1)

# -------------------------------------------------------------------- #
def draw_callback_3d(self, context):
	"""
	Draw 3d circles indicator.
	"""

	region = context.region
	rv3d = context.region_data

	if self.light and (context.active_object is not None):
		light = self.light
		color = context.preferences.themes[0].view_3d.object_active
		if self.action == "shadow":
			coords = [list(light.Lumiere.shadow), list(light.location)]
		else:
			coords = [list(light.Lumiere.hit), list(light.location)]
		draw_shader(self, color, 1, 'LINES', coords, size=2)

# -------------------------------------------------------------------- #
def draw_shader(self, color, alpha, type, coords, size=1, indices=None):
	""" Create a batch for a draw type """
	bgl.glEnable(bgl.GL_BLEND)
	bgl.glEnable(bgl.GL_LINE_SMOOTH)
	bgl.glPointSize(size)
	bgl.glLineWidth(size)
	try:
		if len(coords[0])>2:
			shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
		else:
			shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
		batch = batch_for_shader(shader, type, {"pos": coords}, indices=indices)
		shader.bind()
		shader.uniform_float("color", (color[0], color[1], color[2], alpha))
		batch.draw(shader)
		bgl.glLineWidth(1)
		bgl.glPointSize(1)
		bgl.glDisable(bgl.GL_LINE_SMOOTH)
		bgl.glDisable(bgl.GL_BLEND)
	except:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		self.report({'ERROR'}, str(exc_value))
