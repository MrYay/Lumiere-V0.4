import bpy

from ..lumiere_utils import (
	get_mat_name,
	)

# -------------------------------------------------------------------- #
# Platform
def platform_mat(platform):
	"""Cycles material nodes for the platform"""

	# Create a new material for cycles Engine.
	if bpy.context.scene.render.engine != 'CYCLES':
		bpy.context.scene.render.engine = 'CYCLES'

	if platform.active_material is None:
		mat = bpy.data.materials.new(platform.name)

		# Use nodes by default
		mat.use_nodes = True

	# Assign the material to the light
	platform.active_material = mat

	# Clear node tree
	mat.node_tree.nodes.clear()


#### GRADIENTS ###
	# Texture coordinate
	coord = mat.node_tree.nodes.new(type = 'ShaderNodeTexCoord')
	coord.location = (-1580.0, -260.0)

	# Separate generated XYZ
	sep_gen_xyz = mat.node_tree.nodes.new(type = 'ShaderNodeSeparateXYZ')
	sep_gen_xyz.name = "Separate generate"
	mat.node_tree.links.new(coord.outputs[0], sep_gen_xyz.inputs[0])
	sep_gen_xyz.location = (-1400.0,-40.0)

	# Separate object XYZ
	sep_ob_xyz = mat.node_tree.nodes.new(type = 'ShaderNodeSeparateXYZ')
	sep_ob_xyz.name = "Separate object"
	mat.node_tree.links.new(coord.outputs[3], sep_ob_xyz.inputs[0])
	sep_ob_xyz.location = (-1400.0, -400.0)

	# Invert map range object
	map_invert = mat.node_tree.nodes.new(type = 'ShaderNodeMapRange')
	mat.node_tree.links.new(sep_ob_xyz.outputs[2], map_invert.inputs[0])
	map_invert.inputs[1].default_value = 0
	map_invert.inputs[2].default_value = 1
	map_invert.inputs[3].default_value = 1
	map_invert.inputs[4].default_value = -10
	map_invert.location = (-1220.0, -400.0)

	# Multiply specular
	multiply_spec = mat.node_tree.nodes.new(type = 'ShaderNodeMath')
	mat.node_tree.links.new(map_invert.outputs[0], multiply_spec.inputs[0])
	mat.node_tree.links.new(sep_gen_xyz.outputs[0], multiply_spec.inputs[1])
	multiply_spec.name = "Multiply specular"
	multiply_spec.operation = 'MULTIPLY'
	multiply_spec.location = (-860.0, -200.0)

	# Multiply roughness
	multiply_roug = mat.node_tree.nodes.new(type = 'ShaderNodeMath')
	mat.node_tree.links.new(sep_gen_xyz.outputs[0], multiply_roug.inputs[0])
	mat.node_tree.links.new(map_invert.outputs[0], multiply_roug.inputs[1])
	multiply_roug.name = "Multiply roughness"
	multiply_roug.operation = 'MULTIPLY'
	multiply_roug.location = (-860.0, -460.0)

	# Specular range
	map_spec = mat.node_tree.nodes.new(type = 'ShaderNodeMapRange')
	mat.node_tree.links.new(multiply_spec.outputs[0], map_spec.inputs[0])
	map_spec.name = "Specular range"
	map_spec.inputs[1].default_value = 0
	map_spec.inputs[2].default_value = 1
	map_spec.inputs[3].default_value = 0
	map_spec.inputs[4].default_value = 1
	map_spec.location = (-660.0, -160.0)

	# Roughness range
	map_rough = mat.node_tree.nodes.new(type = 'ShaderNodeMapRange')
	mat.node_tree.links.new(multiply_roug.outputs[0], map_rough.inputs[0])
	map_rough.name = "Roughness range"
	map_rough.inputs[1].default_value = 0
	map_rough.inputs[2].default_value = 1
	map_rough.inputs[3].default_value = 0
	map_rough.inputs[4].default_value = 1
	map_rough.location = (-660.0, -400.0)

	# Color Ramp Node
	colramp = mat.node_tree.nodes.new(type="ShaderNodeValToRGB")
	mat.node_tree.links.new(sep_gen_xyz.outputs[0], colramp.inputs['Fac'])
	colramp.name = "Color ramp"
	colramp.color_ramp.elements[0].color = (1,1,1,1)
	colramp.inputs[0].default_value = 0
	colramp.location = (-580.0, 100.0)

	# BSDF
	bsdf = mat.node_tree.nodes.new(type = 'ShaderNodeBsdfPrincipled')
	bsdf.name = "BSDF"
	mat.node_tree.links.new(map_spec.outputs[0], bsdf.inputs[5])
	mat.node_tree.links.new(map_rough.outputs[0], bsdf.inputs[7])
	bsdf.location = (-200.0, 140.0)

	# RGB Node
	color = mat.node_tree.nodes.new(type = 'ShaderNodeRGB')
	color.outputs[0].default_value = (0, 0, 0, 1)
	color.location = (-380.0, 360.0)

	# Transparent
	transparent = mat.node_tree.nodes.new('ShaderNodeBsdfTransparent')
	transparent.name = "Transparent"
	mat.node_tree.links.new(color.outputs[0], transparent.inputs[0])
	transparent.location = (-200.0, 480.0)

	# Translucent
	translucent = mat.node_tree.nodes.new('ShaderNodeBsdfTranslucent')
	translucent.name = "Translucent"
	mat.node_tree.links.new(color.outputs[0], translucent.inputs[0])
	translucent.location = (-200.0, 360.0)

	# Add shader 1
	add1 = mat.node_tree.nodes.new(type="ShaderNodeAddShader")
	add1.name = "Add1"
	mat.node_tree.links.new(transparent.outputs[0], add1.inputs[0])
	mat.node_tree.links.new(translucent.outputs[0], add1.inputs[1])
	add1.location = (-20.0, 360.0)

	# Add shader 2
	add2 = mat.node_tree.nodes.new(type="ShaderNodeAddShader")
	add2.name = "Add2"
	mat.node_tree.links.new(add1.outputs[0], add2.inputs[0])
	mat.node_tree.links.new(bsdf.outputs[0], add2.inputs[1])
	add2.location = (160.0, 360.0)

	# Geometry
	geometry = mat.node_tree.nodes.new('ShaderNodeNewGeometry')
	geometry.name = "Geometry"
	geometry.location = (160.0, 740.0)

	# Transparent camera
	transparent_cam = mat.node_tree.nodes.new('ShaderNodeBsdfTransparent')
	transparent_cam.name = "Transparent camera"
	mat.node_tree.links.new(color.outputs[0], transparent_cam.inputs[0])
	transparent_cam.location = (160.0, 480.0)

	# Mix Shader 1
	mix1 = mat.node_tree.nodes.new(type="ShaderNodeMixShader")
	mix1.name = "Mix1"
	mat.node_tree.links.new(geometry.outputs[6], mix1.inputs[0])
	mat.node_tree.links.new(add2.outputs[0], mix1.inputs[1])
	mat.node_tree.links.new(transparent_cam.outputs[0], mix1.inputs[2])
	mix1.location = (340.0, 520.0)

#### OUTPUT ###

	# Output Shader Node
	output = mat.node_tree.nodes.new(type = 'ShaderNodeOutputMaterial')
	output.location = (620.0, 380.0)
	output.select
	#Link them together
	mat.node_tree.links.new(add2.outputs[0], output.inputs['Surface'])

# Update material
# -------------------------------------------------------------------- #
def platform_update_mat(self, context):
	"""Update the material nodes of the platform"""

	# Get the platform
	platform = context.object

	mat = get_mat_name(platform)
	sep_gen_xyz = mat.node_tree.nodes["Separate generate"]
	specular_range = mat.node_tree.nodes["Specular range"]
	specular_value = mat.node_tree.nodes["Specular range"]
	roughness_value = mat.node_tree.nodes["Roughness range"]
	bsdf = mat.node_tree.nodes["BSDF"]
	rgb = mat.node_tree.nodes["RGB"]
	rgb_val = platform.Lumiere_platform.translucency
	if platform.Lumiere_platform.translucency > 0 and  bpy.context.scene.render.engine != 'CYCLES':
		mat.shadow_method = 'NONE'
	else:
		mat.shadow_method = 'OPAQUE'


	specular_range.inputs[1].default_value = platform.Lumiere_platform.specular_range
	specular_value.inputs[4].default_value = platform.Lumiere_platform.specular_value
	roughness_value.inputs[4].default_value = platform.Lumiere_platform.roughness_value
	bsdf.inputs[0].default_value = platform.Lumiere_platform.platform_color
	rgb.outputs[0].default_value = (rgb_val, rgb_val, rgb_val, 1)
