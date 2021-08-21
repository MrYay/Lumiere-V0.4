import bpy
import bmesh
from mathutils import (
	Vector,
	Matrix,
	)

from math import (
	radians,
	)

from ..lumiere_utils import (
	get_collection,
	)

from .lumiere_platform_materials import (
	platform_mat,
	)

# -------------------------------------------------------------------- #
# Platform
def create_platform(platform_name = "Platform"):
	"""Create the platform with modifiers"""

	# Initialize the mesh props
	vertices = []
	edges = []
	faces = []

	# 1 Unit mesh
	vertices = [
			 Vector((-.5, .5, 0)),
			 Vector((.5, .5, 0)),
			 Vector((.5, -.5, 0)),
			 Vector((-.5, -.5, 0)),
			]

	faces = [[0, 1, 2, 3]]

	# Set the Lumiere Platform as the active layer collection
	primary_col, light_col, platform_col = get_collection()

	primary_layer = bpy.context.view_layer.layer_collection.children[primary_col.name]
	bpy.context.view_layer.active_layer_collection = primary_layer.children[platform_col.name]

	# Create a new object and link it to the scene
	mesh = bpy.data.meshes.new('Platform')
	mesh.from_pydata(vertices, edges, faces)
	mesh.update()

	# Link to collection
	platform = bpy.data.objects.new("Platform", mesh)
	platform_col.objects.link(platform)

	# Make the object active
	bpy.ops.object.select_all(action='DESELECT')
	platform.select_set(state=True)
	bpy.context.view_layer.objects.active = platform

	# Add the material
	platform_mat(platform)

	# Set back the active collection to the master collection
	bpy.context.view_layer.active_layer_collection =  bpy.context.view_layer.layer_collection

	# Add a default height of one unit
	platform.Lumiere_platform.height = 1

# -------------------------------------------------------------------- #
def add_vertice(self, context, bm, vertices, vert1, vert2, face1, face2, face3, face4, depth=0, height=0):
	"""Add vertices for the wall of the platform"""
	platform = bpy.data.objects[self.id_data.name]
	depth *= platform.Lumiere_platform.scale

	vertices.append(bm.verts.new((bm.verts[vert1].co.x,bm.verts[vert1].co.y - depth , bm.verts[vert1].co.z + height)))
	bm.verts.ensure_lookup_table()
	vertices.append(bm.verts.new((bm.verts[vert2].co.x,bm.verts[vert2].co.y - depth, bm.verts[vert2].co.z + height)))
	bm.verts.ensure_lookup_table()
	bm.faces.new((bm.verts[face1], bm.verts[face2], bm.verts[face3], bm.verts[face4]))

# -------------------------------------------------------------------- #
def extrude_edge(self, context, bm, bevel, height=0, box = False):

	edges_to_bevel = []
	for i, v in enumerate(bevel["verts"]):
		for idx, e in enumerate(v.link_edges):
			if e not in edges_to_bevel:
				edges_to_bevel.append(e)

	if height > 0:
		extrude = bmesh.ops.extrude_edge_only(bm, edges=edges_to_bevel)
		edges=[e for e in extrude['geom'] if isinstance(e, bmesh.types.BMEdge)]

		# Add a ceiling
		if box:
			faces = bmesh.ops.edgenet_prepare(bm, edges=edges)
			faces = bmesh.ops.edgenet_fill(bm, edges=faces["edges"])
			for edge in edges:
				edges_to_bevel.append(edge)

		bmesh.ops.translate(bm, vec=Vector((0,0,height)), verts=[e for e in extrude['geom'] if isinstance(e, bmesh.types.BMVert)])


	return edges_to_bevel
# -------------------------------------------------------------------- #
def bevel_edges(self,context, bm):
	"""Update the platform"""
	platform = bpy.data.objects[self.id_data.name]
	contour_edges = []

	# Add a first stage bevel to the platform
	if not 'Lumiere_Bevel1' in list(m.name for m in platform.modifiers):
		bpy.ops.object.modifier_add(type='BEVEL')
		mod = context.object.modifiers[-1]
		mod.name = 'Lumiere_Bevel1'
		mod.limit_method = 'ANGLE'
		mod.angle_limit = radians(30)
		mod.width = 0.03
		mod.profile = 0.699099
		mod.segments = 3
		mod.use_clamp_overlap = True
		mod.loop_slide = True

		#2.9
		if float(bpy.app.version_string[:3]) > 2.8 : #if bpy.app.version[1] > 83 :
			mod.affect = 'VERTICES' if platform.Lumiere_platform.height == 0 else 'EDGES'
		else :
			mod.use_only_vertices = True if platform.Lumiere_platform.height == 0 else False

	else:
		mod = platform.modifiers['Lumiere_Bevel1']
		mod.limit_method = 'ANGLE'
		mod.angle_limit = radians(30)
		mod.width = platform.Lumiere_platform.bevel_offset
		mod.profile = platform.Lumiere_platform.bevel_profil
		mod.segments = platform.Lumiere_platform.bevel_segment
		mod.use_clamp_overlap = True
		mod.loop_slide = True

		# 2.9
		if float(bpy.app.version_string[:3]) > 2.8 :
			mod.affect = 'VERTICES' if platform.Lumiere_platform.height == 0 else 'EDGES'
		else:
			mod.use_only_vertices = True if platform.Lumiere_platform.height == 0 else False

# -------------------------------------------------------------------- #
def update_platform(self,context):
	"""Update the platform"""

	platform = bpy.data.objects[self.id_data.name]
	scale = platform.Lumiere_platform.scale
	scale_x = platform.Lumiere_platform.scale_x * scale
	scale_y = platform.Lumiere_platform.scale_y * scale
	height = platform.Lumiere_platform.height * scale
	ceiling = platform.Lumiere_platform.ceiling

	# Get the data and delete it
	bm = bmesh.new()
	bm.from_mesh(platform.data)
	bm.clear()

	vertices = []
	faces = []

	# Create the base mesh of 1 unit
	vertices.append(bm.verts.new((-scale_x, scale_y, 0)))
	vertices.append(bm.verts.new((-scale_x, -scale_y, 0)))
	vertices.append(bm.verts.new((scale_x, -scale_y, 0)))
	vertices.append(bm.verts.new((scale_x, scale_y, 0)))
	bm.verts.ensure_lookup_table()

	for idx, vert in enumerate(vertices):
		if idx > 0:
			bm.edges.new([vertices[idx-1],vertices[idx]])
	bm.faces.new((vertices[0], vertices[1], vertices[2], vertices[3]))
	bm.edges.index_update()

	if platform.Lumiere_platform.height > 0:
		if platform.Lumiere_platform.platform_type == "L_curve" :
			# Back wall
			add_vertice(self,context, bm, vertices, 0, 3, 0, 3, -1, -2, 0, height)

		elif platform.Lumiere_platform.platform_type == "S_curve":
			# Back wall
			add_vertice(self,context, bm, vertices, 0, 3, 0, 3, -1, -2, 0, height)

			# Bottom wall
			add_vertice(self,context, bm, vertices, 1, 2, 1, -2, -1, 2, 0, -height)

		elif platform.Lumiere_platform.platform_type == "C_curve":
			# Back wall
			add_vertice(self,context, bm, vertices, 0, 3, 0, 3, -1, -2, 0, height)

			# Top wall
			add_vertice(self,context, bm, vertices, 4, 5, 4, 5, -1, -2, ceiling, 0)

		elif platform.Lumiere_platform.platform_type == "3_walls":
			bevel=  {'faces': [], 'edges': [], 'verts': []}
			bevel["verts"] = vertices[0],vertices[3]
			extrude_edge(self, context, bm, bevel, height)

		elif platform.Lumiere_platform.platform_type == "Box":
			bevel=  {'faces': [], 'edges': [], 'verts': []}
			bevel["verts"] = vertices[0],vertices[3]
			extrude_edge(self, context, bm, bevel, height, box = True)

		elif platform.Lumiere_platform.platform_type == "Corner":
			bevel=  {'faces': [], 'edges': [], 'verts': []}
			bevel["verts"] = vertices[0],
			extrude_edge(self, context, bm, bevel, height)

			# Rotate 45°
			bmesh.ops.rotate(
				bm,
				verts=bm.verts[:],
				cent=(0.0, 0.0, 0.0),
				matrix=Matrix.Rotation(radians(-45.0), 3, 'Z'))

	bevel_edges(self,context, bm)

	bm.faces.index_update()

	# Enable shade smooth
	if platform.Lumiere_platform.shade_smooth :
		for f in bm.faces:
			f.smooth = True

		platform.data.use_auto_smooth = True
		platform.data.auto_smooth_angle = radians(89)
	else:
		platform.data.use_auto_smooth = False

	bm.to_mesh(platform.data)
	bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
	bm.free()
	platform.data.update()
	platform.lock_scale[:] = (True, True, True)
