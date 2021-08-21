import bpy
import os
import json
import bgl
import time


from bpy_extras import view3d_utils
from mathutils import (
				Vector,
				Matrix,
				Quaternion,
				Euler
				)

from math import (
	degrees,
	radians,
	floor,
	sin,
	asin,
	tan,
	cos,
	sqrt,
	atan,
	atan2,
	acos,
	pi,
	)

# -------------------------------------------------------------------- #
def raycast_shadow(self, event, context, range, shadow_hit=None, ray_max=1000.0):
	"""Compute the location and rotation of the light from the angle or normal of the targeted face off the object"""

	length_squared = 0
	scene = context.scene
	light = context.active_object
	rv3d = context.region_data
	region = context.region
	coord = (event.mouse_region_x, event.mouse_region_y)
	primary_col, light_col, platform_col = get_collection()

	# Direction vector from the viewport to 2d coord
	view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, (coord))
	# 3d view origin vector from the region
	ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, (coord))
	# Define a default direction vector
	ray_target = ray_origin + (view_vector * ray_max)

	# Find the closest object
	best_length_squared = -1
	length_squared = 0
	best_obj = None

	# Find the position of the shadow
	for obj_trgt, matrix_trgt in visible_objects_and_duplis(self, context, light):
		ray_cast_origin = matrix_trgt.inverted() @ ray_origin
		ray_cast_target = matrix_trgt.inverted() @ ray_target

		if obj_trgt.type == 'MESH':

			hit, normal_trgt, face_index = obj_ray_cast(obj_trgt, matrix_trgt, ray_cast_origin, ray_cast_target, invert=False)

			if hit is not None :

				hit_world = matrix_trgt @ hit
				length_squared = (hit_world - light.location).length_squared

				if best_obj is None or length_squared > best_length_squared:
					best_length_squared = length_squared
					best_obj = obj_trgt

					# Get the normal of the face from the targeted object
					normal = matrix_trgt.to_3x3().inverted().transposed() @ normal_trgt
					normal.normalize()

					# Define the direction based on the normal of the targeted object, the view angle or the bounding box
					if light.parent == best_obj:
						light.Lumiere.shadow = (0,0,0)
						length_squared = -1
					else:
						light.Lumiere.shadow = hit_world
						reflect_dir = Vector(shadow_hit) - Vector(light.Lumiere.shadow)
						reflect_dir.normalize()
						light_loc = Vector(shadow_hit) + (reflect_dir * range)

						_matrix_trgt = matrix_trgt
						_hit = hit
						_light_loc = light_loc
						_direction = reflect_dir

	# Define location, rotation and scale
	if length_squared > 0 :

		rotaxis = (_direction.to_track_quat('Z','Y')).to_euler()
		light.location = Vector((_light_loc[0], _light_loc[1], _light_loc[2]))

		# Update rotation and tilt for spherical coordinate
		x,y,z = light.location - Vector((light.Lumiere.hit))
		r = sqrt(x**2 + y**2 + z**2)
		theta = atan2(y, x)
		if degrees(theta) < 0:
			theta = radians(degrees(theta) + 360)
		light.Lumiere.rotation = degrees(theta)
		phi = acos( z / r )

		light.Lumiere.tilt = degrees(phi)
		light.rotation_euler = rotaxis

		light.Lumiere.direction = _direction

		light.Lumiere.light_mode = "None"

# -------------------------------------------------------------------- #
def raycast_light(self, event, context, range, ray_max=1000.0):
	"""Compute the location and rotation of the light from the angle or normal of the targeted face off the object"""

	length_squared = 0
	scene = context.scene
	light = context.active_object
	rv3d = context.region_data
	region = context.region
	coord = (event.mouse_region_x, event.mouse_region_y)
	primary_col, light_col, platform_col = get_collection()

	# Direction vector from the viewport to 2d coord
	view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, (coord))
	# 3d view origin vector from the region
	ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, (coord))
	# Define a default direction vector
	ray_target = ray_origin + (view_vector * ray_max)

	invert = -1 if light.Lumiere.invert_ray_cast else 1

	# Find the closest object
	best_length_squared = -1.0
	best_obj = None
	# Find the position of the light using the reflect angle and the object targeted normal
	for obj_trgt, matrix_trgt in visible_objects_and_duplis(self, context, light):
		ray_cast_origin = matrix_trgt.inverted() @ ray_origin
		ray_cast_target = matrix_trgt.inverted() @ ray_target

		if obj_trgt.type == 'MESH':
			hit, normal_trgt, face_index = obj_ray_cast(obj_trgt, matrix_trgt, ray_cast_origin, ray_cast_target)

			if hit is not None :

				hit_world = matrix_trgt @ hit
				length_squared = (hit_world - ray_origin).length_squared

				if best_obj is None or length_squared < best_length_squared:
					best_length_squared = length_squared
					best_obj = obj_trgt

					# Get the normal of the face from the targeted object
					normal = matrix_trgt.to_3x3().inverted().transposed() @ normal_trgt
					normal.normalize()

					# Define the direction based on the normal of the targeted object, the view angle or the bounding box
					if light.Lumiere.reflect_angle == "Accurate":
						reflect_dir = (view_vector).reflect(normal)*invert

					elif light.Lumiere.reflect_angle == "Normal":
						if obj_trgt.name in light_col.all_objects:
							reflect_dir = -normal*invert
						else:
							reflect_dir = normal*invert

					elif light.Lumiere.reflect_angle == "Estimated":
						if light.Lumiere.auto_bbox_center:
							if light.Lumiere.estimated_type == "Collection":
								bbox_col = []
								for obj in obj_trgt.users_collection[0].all_objects:
									local_bbox_center = 0.125 * sum((Vector(b) for b in obj.bound_box), Vector())
									global_bbox_center = obj.matrix_world @ local_bbox_center
									bbox_col.append(tuple(global_bbox_center))

								x,y,z=zip(*bbox_col)
								center=(max(x)+min(x))/2, (max(y)+min(y))/2, (max(z)+min(z))/2
								global_bbox_center = Vector(center)
							else:
								local_bbox_center = 0.125 * sum((Vector(b) for b in obj_trgt.bound_box), Vector())
								global_bbox_center = obj_trgt.matrix_world @ local_bbox_center
						else:
							global_bbox_center = Vector(light.Lumiere.bbox_center)
						light.Lumiere.bbox_center = global_bbox_center
						reflect_dir = ((matrix_trgt @ hit) - global_bbox_center)*invert
						reflect_dir.normalize()

					# Define light location : Hit + Direction + Range
					light_loc = (matrix_trgt @ hit) + (reflect_dir * range)

					_matrix_trgt = matrix_trgt
					_hit = hit
					_light_loc = light_loc
					_direction = reflect_dir

					# Parent the light to the target object
					light.parent = obj_trgt
					light.matrix_parent_inverse = matrix_trgt.inverted()

	# Define location, rotation and scale
	if length_squared > 0:

		# Point the light in another direction
		if self.point :
			track  = light.location - Vector(_matrix_trgt @ _hit)
			rotaxis = (track.to_track_quat('Z','Y')).to_euler()
		else :
			rotaxis = (_direction.to_track_quat('Z','Y')).to_euler()
			light.location = Vector((_light_loc[0], _light_loc[1], _light_loc[2]))

		light.Lumiere.hit = (_matrix_trgt @ _hit)

		# Update rotation and tilt for spherical coordinate
		x,y,z = light.location - Vector((light.Lumiere.hit))
		r = sqrt(x**2 + y**2 + z**2)
		theta = atan2(y, x)
		if degrees(theta) < 0:
			theta = radians(degrees(theta) + 360)
		light.Lumiere.rotation = degrees(theta)
		phi = acos( z / r )

		light.Lumiere.tilt = degrees(phi)
		light.rotation_euler = rotaxis

		light.Lumiere.direction = _direction
		light.Lumiere.light_mode = "None"

		#Find the location of the shadow gizmo
		shadow_helper(self, context, light)

# -------------------------------------------------------------------- #
def shadow_helper(self, context, light):
	best_length_squared = -1
	length_squared = 0
	best_obj = None
	# Find the position of the shadow helper on the farest object from the light
	for obj_shd, matrix_shd in visible_objects_and_duplis(self, context, light):
		ray_cast_origin = matrix_shd.inverted() @ Vector((light.location))
		ray_cast_target = matrix_shd.inverted() @ Vector((light.Lumiere.hit))
		if obj_shd.type == 'MESH':
			hit, normal_trgt, face_index = obj_ray_cast(obj_shd, matrix_shd, ray_cast_origin, ray_cast_target, invert=False)

			if light.parent == obj_shd:
				light.Lumiere.shadow = (0,0,0)

			if hit is not None and light.parent != obj_shd :
				hit_world = matrix_shd @ hit
				# length_squared = (hit_world - light.location).length_squared
				# length_hit = (Vector((light.Lumiere.hit)) - light.location).length_squared
				length_squared = (hit_world - light.location).length_squared
				# print(length_hit)
				# print(length_shd)
				if length_squared > best_length_squared:
					best_length_squared = length_squared
					best_obj = obj_shd
					light.Lumiere.shadow = hit_world

# -------------------------------------------------------------------- #
def visible_objects_and_duplis(self, context, light):
	# Select the targeted object
	depsgraph =  context.evaluated_depsgraph_get()
	primary_col, light_col, platform_col = get_collection()
	if light.Lumiere.target :
		obj_trgt = light.Lumiere.target
		yield (obj_trgt, obj_trgt.matrix_world.copy())
	else:
		for dup in depsgraph.object_instances:
			if dup.object.name not in light_col.all_objects or \
			(dup.object.name in light_col.all_objects and \
			(dup.object.Lumiere.color_type == 'Reflector' and dup.object.data.name != light.data.name)):
				# Ignore the parent object when in shadow mode
				# if (shadow and (dup.object.name != light.parent.name)) or not shadow :

				if dup.is_instance:
					yield (dup.instance_object, dup.instance_object.matrix_world.copy())
				else:
					yield (dup.object.original, dup.object.original.matrix_world.copy())
# -------------------------------------------------------------------- #
def obj_ray_cast(obj_trgt, matrix_trgt, ray_cast_origin, ray_cast_target, invert=False):

	# Get the ray direction from the view angle to the targeted object
	ray_cast_direction = ray_cast_target - ray_cast_origin

	# Cast the ray to the targeted object
	success, hit, normal, face_index = obj_trgt.ray_cast(ray_cast_origin, ray_cast_direction)

	# Find the back of the object
	# https://github.com/nortikin/sverchok/issues/660
	if invert:
		max_intersections = 10
		fudge_distance = 0.0001
		direction = (ray_cast_direction - hit)
		dir_len = direction.length
		amount = fudge_distance / dir_len

		i = 1
		while (face_index != -1):

			# Linear interpolation
			hit = hit.lerp(direction, amount)
			success2, hit2, normal2, face_index2 = obj_trgt.ray_cast(hit, ray_cast_direction)
			if face_index2 == -1:
				break
			else:
				hit = hit2
				success = success2
				normal = normal2
				face_index = face_index2
			i += 1
			if i > max_intersections:
				break

	if success:
		return hit, normal, face_index
	else:
		return None, None, None

# -------------------------------------------------------------------- #
def create_2d_circle(step, radius, rotation = 0, center_x=0, center_y=0):
	""" Create the vertices of a 2d circle at (0,0) """
	#https://stackoverflow.com/questions/8487893/generate-all-the-points-on-the-circumference-of-a-circle
	indices = []

	verts = [(center_x, center_y)] + [(
			cos(2*pi / step*x + rotation)*radius + center_x,
			sin(2*pi / step*x + rotation)*radius + center_y
			) for x in range(0, step+1)]

	for idx in range(len(verts) - 1):
		i1 = idx+1
		i2 = idx+2 if idx+2 <= step else 1
		indices.append((0,i1,i2))

	return(verts, indices)

# -------------------------------------------------------------------- #
def draw_circle(center_circle, radius_circle, steps):
	""" Return the coordinates + indices of a circle using a triangle fan """
	indices = []
	center_x, center_y = center_circle
	radiusx = radius_circle[0] - center_circle[0]
	radiusy = radius_circle[1] - center_circle[1]
	radius = sqrt(radiusx**2 + radiusy**2)
	rotation = radians(radius_circle[1] - center_circle[1]) / 2

	# Get the vertices of a 2d circle
	verts, indices = create_2d_circle(steps, radius, rotation, center_x, center_y)

	return(verts, indices)

# -------------------------------------------------------------------- #
def export_props_group(self, context, name, light_selected):
	"""Export the group of lights data in JSON format"""

	lumiere_group = {}
	lumiere_group['Group_'+name] = {}

	for light in light_selected:
		lumiere_dict = export_props_light(self, context, light)
		lumiere_group['Group_'+name][light.name] = lumiere_dict[light.name]

	return(lumiere_group)

# -------------------------------------------------------------------- #
def export_props_light(self, context, light):
	"""Export the current light data in JSON format"""

	lumiere_dict = {}

	lumiere_dict[light.name] = {}
	lumiere_dict[light.name]['Lumiere'] = light['Lumiere'].to_dict()
	lumiere_dict[light.name]['Lumiere']['light_type'] = light.Lumiere.light_type
	lumiere_dict[light.name]['rotation'] = tuple(light.matrix_world.to_euler())
	lumiere_dict[light.name]['scale'] = tuple(light.scale)
	lumiere_dict[light.name]['location'] = tuple(light.location)

	mat = get_mat_name(light)
	if light.type == "LIGHT":
		colramp = light.data.node_tree.nodes["ColorRamp"].color_ramp
		falloff_ramp = light.data.node_tree.nodes["Falloff colRamp"].color_ramp
		lumiere_dict[light.name]['smooth'] = light.data.node_tree.nodes["Light Falloff"].inputs[1].default_value
		if light.data.type == "AREA" :
			lumiere_dict[light.name]['shape'] = light.data.shape
	else:
		colramp = mat.node_tree.nodes['ColorRamp'].color_ramp
		falloff_ramp = mat.node_tree.nodes['Falloff colRamp'].color_ramp
		lumiere_dict[light.name]['smooth'] = mat.node_tree.nodes['Light Falloff'].inputs[1].default_value

	# Gradient coloramp
	if light.Lumiere.color_type in ("Linear", "Spherical", "Gradient"):
		lumiere_dict[light.name]['gradient'] = {}
		lumiere_dict[light.name]['interpolation'] = colramp.interpolation
		for i in range(len(colramp.elements)):
			lumiere_dict[light.name]['gradient'].update({colramp.elements[i].position: colramp.elements[i].color[:]})

	# Falloff coloramp
	lumiere_dict[light.name]['falloff_ramp'] = {}
	for i in range(len(falloff_ramp.elements)):
		lumiere_dict[light.name]['falloff_ramp'].update({falloff_ramp.elements[i].position: falloff_ramp.elements[i].color[:]})

	return(lumiere_dict)

# -------------------------------------------------------------------- #
def get_mat_name(light):
	"""Return the name of the material of the light"""
	if light.type == 'MESH':
		mat = light.active_material
	else:
		mat = light.data

	return(mat)

# -------------------------------------------------------------------- #
def get_lumiere_dict():
	"""Return the file of the exported lights in a dict format"""

	current_file_dir = os.path.dirname(__file__)
	file_name = os.path.join(current_file_dir, "lumiere_dictionary.json")

		# Try to open the Lumiere export dictionary
	try:
		with open(file_name, 'r', encoding='utf-8') as file:
			my_dict = json.loads(file.read())
			file.close()
	except :
		# print("\n[Lumiere ERROR]\n")
		# import traceback
		# traceback.print_exc()
		my_dict = {}
	return(my_dict)

# -------------------------------------------------------------------- #
def update_lumiere_dict(my_dict):
	"""Update the file of the exported lights"""
	current_file_dir = os.path.dirname(__file__)

	with open(current_file_dir + "\\" + "lumiere_dictionary.json", "w", encoding='utf-8') as file:
		json.dump(my_dict, file, sort_keys=True, indent=4, ensure_ascii=False)
	file.close()

# -------------------------------------------------------------------- #
def cartesian_coordinates(r, theta, phi, hit=(0,0,0)):
	"""Return the cartesian coordinates from a radius, inclination (phi) and azimuth (theta)"""

	# https://en.wikipedia.org/wiki/Spherical_coordinate_system
	x = r * sin(phi) * cos(theta) + hit[0]
	y = r * sin(phi) * sin(theta) + hit[1]
	z = r * cos(phi) + hit[2]

	return Vector((x, y, z))

# -------------------------------------------------------------------- #
def getSunPosition(localTime = 12.0, latitude = 48.87, longitude = 2.67, northOffset = 1.00, utcZone = 0, month = 12, day = 22, year = 2012, distance = 5):
	"""
	Compute the sun position based on latitude and longitude
	The sun position is from the addon 'sun_position' from Michael Martin (xaire)
	https://archive.blender.org/wiki/index.php/Extensions:2.6/Py/Scripts/3D_interaction/Sun_Position/
	"""

	longitude *= -1                 # for internal calculations
	utcTime = localTime + utcZone   # Set Greenwich Meridian Time

	if latitude > 89.93:            # Latitude 90 and -90 gives
		latitude = radians(89.93)  # erroneous results so nudge it
	elif latitude < -89.93:
		latitude = radians(-89.93)
	else:
		latitude = radians(latitude)

	t = julianTimeFromY2k(utcTime, year, month, day)

	e = radians(obliquityCorrection(t))
	L = apparentLongitudeOfSun(t)
	solarDec = sunDeclination(e, L)
	eqtime = calcEquationOfTime(t)

	timeCorrection = (eqtime - 4 * longitude) + 60 * utcZone
	trueSolarTime = ((utcTime - utcZone) * 60.0 + timeCorrection) % 1440

	hourAngle = trueSolarTime / 4.0 - 180.0
	if hourAngle < -180.0:
		hourAngle += 360.0

	csz = (sin(latitude) * sin(solarDec) +
		   cos(latitude) * cos(solarDec) *
		   cos(radians(hourAngle)))

	if csz > 1.0:
		csz = 1.0
	elif csz < -1.0:
		csz = -1.0

	zenith = acos(csz)

	azDenom = cos(latitude) * sin(zenith)

	if abs(azDenom) > 0.001:
		azRad = ((sin(latitude) *
				  cos(zenith)) - sin(solarDec)) / azDenom
		if abs(azRad) > 1.0:
			azRad = -1.0 if (azRad < 0.0) else 1.0
		azimuth = 180.0 - degrees(acos(azRad))
		if hourAngle > 0.0:
			azimuth = -azimuth
	else:
		azimuth = 180.0 if (latitude > 0.0) else 0.0

	if azimuth < 0.0:
		azimuth = azimuth + 360.0

	exoatmElevation = 90.0 - degrees(zenith)

	if exoatmElevation > 85.0:
		refractionCorrection = 0.0
	else:
		te = tan(radians(exoatmElevation))
		if exoatmElevation > 5.0:
			refractionCorrection = (
				58.1 / te - 0.07 / (te ** 3) + 0.000086 / (te ** 5))
		elif (exoatmElevation > -0.575):
			s1 = (-12.79 + exoatmElevation * 0.711)
			s2 = (103.4 + exoatmElevation * (s1))
			s3 = (-518.2 + exoatmElevation * (s2))
			refractionCorrection = 1735.0 + exoatmElevation * (s3)
		else:
			refractionCorrection = -20.774 / te

		refractionCorrection = refractionCorrection / 3600

	solarElevation = 90.0 - degrees(zenith)

	solarAzimuth = azimuth + northOffset

	Sun_AzNorth = solarAzimuth

	Sun_Theta = pi / 2 - radians(solarElevation)
	Sun_Phi = radians(solarAzimuth) * -1

	location = setSunPosition(Sun_Theta, Sun_Phi, distance)

	rotation = ((radians(solarElevation - 90), 0, radians(-solarAzimuth)))

	return location, rotation

def setSunPosition(Sun_Theta, Sun_Phi, distance = 1):

	locX = sin(Sun_Phi) * sin(-Sun_Theta) * distance
	locY = sin(Sun_Theta) * cos(Sun_Phi) * distance
	locZ = cos(Sun_Theta) * distance

	try:
		return (locX, locY, locZ)
	except:
		pass


def sunDeclination(e, L):
	return (asin(sin(e) * sin(L)))


def calcEquationOfTime(t):
	epsilon = obliquityCorrection(t)
	ml = radians(meanLongitudeSun(t))
	e = eccentricityEarthOrbit(t)
	m = radians(meanAnomalySun(t))
	y = tan(radians(epsilon) / 2.0)
	y = y * y
	sin2ml = sin(2.0 * ml)
	cos2ml = cos(2.0 * ml)
	sin4ml = sin(4.0 * ml)
	sinm = sin(m)
	sin2m = sin(2.0 * m)
	etime = (y * sin2ml - 2.0 * e * sinm + 4.0 * e * y *
			 sinm * cos2ml - 0.5 * y ** 2 * sin4ml - 1.25 * e ** 2 * sin2m)
	return (degrees(etime) * 4)

def obliquityCorrection(t):
	ec = obliquityOfEcliptic(t)
	omega = 125.04 - 1934.136 * t
	return (ec + 0.00256 * cos(radians(omega)))

def obliquityOfEcliptic(t):
	return ((23.0 + 26.0 / 60 + (21.4480 - 46.8150) / 3600 * t -
			(0.00059 / 3600) * t ** 2 + (0.001813 / 3600) * t ** 3))

def julianTimeFromY2k(utcTime, year, month, day):
	century = 36525.0  # Days in Julian Century
	epoch = 2451545.0  # Julian Day for 1/1/2000 12:00 gmt
	jd = getJulianDay(year, month, day)
	return ((jd + (utcTime / 24)) - epoch) / century

def getJulianDay(year, month, day):
	if month <= 2:
		year -= 1
		month += 12
	A = floor(year / 100)
	B = 2 - A + floor(A / 4.0)
	jd = (floor((365.25 * (year + 4716.0))) +
		 floor(30.6001 * (month + 1)) + day + B - 1524.5)
	return jd

def apparentLongitudeOfSun(t):
	return (radians(trueLongitudeOfSun(t) - 0.00569 - 0.00478 *
			sin(radians(125.04 - 1934.136 * t))))


def trueLongitudeOfSun(t):
	return (meanLongitudeSun(t) + equationOfSunCenter(t))

def meanLongitudeSun(t):
	return (280.46646 + 36000.76983 * t + 0.0003032 * t ** 2) % 360


def eccentricityEarthOrbit(t):
	return (0.016708634 - 0.000042037 * t - 0.0000001267 * t ** 2)

def equationOfSunCenter(t):
	m = radians(meanAnomalySun(t))
	c = ((1.914602 - 0.004817 * t - 0.000014 * t ** 2) * sin(m) +
		(0.019993 - 0.000101 * t) * sin(m * 2) +
		 0.000289 * sin(m * 3))
	return c

def meanAnomalySun(t):
	return (357.52911 + t * (35999.05029 - 0.0001537 * t))

# -------------------------------------------------------------------- #
def update_light_direction(self, context, sun_direction, light = None):

	# Credits : https://www.youtube.com/watch?v=YXso7kNzxIU
	xAng = sun_direction[0]
	yAng = sun_direction[1]
	zAng = sun_direction[2]

	vec = Vector((0.0,0.0,1.0))
	xMat = Matrix(((1.0,0.0,0.0), (0.0, cos(xAng), -sin(xAng)), (0.0, sin(xAng), cos(xAng))))
	yMat = Matrix(((cos(yAng), 0.0, sin(yAng)), (0.0, 1.0, 0.0), (-sin(yAng), 0.0, cos(yAng))))
	zMat = Matrix(((cos(zAng), -sin(zAng), 0.0), (sin(zAng), cos(zAng), 0.0), (0.0, 0.0, 1.0)))

	vec = xMat @ vec
	vec = yMat @ vec
	vec = zMat @ vec

	return vec
# -------------------------------------------------------------------- #
def update_sky(self, context, sun_direction, light = None):

	# Credits : https://www.youtube.com/watch?v=YXso7kNzxIU
	xAng = sun_direction[0]
	yAng = sun_direction[1]
	zAng = sun_direction[2]

	vec = Vector((0.0,0.0,1.0))
	xMat = Matrix(((1.0,0.0,0.0), (0.0, cos(xAng), -sin(xAng)), (0.0, sin(xAng), cos(xAng))))
	yMat = Matrix(((cos(yAng), 0.0, sin(yAng)), (0.0, 1.0, 0.0), (-sin(yAng), 0.0, cos(yAng))))
	zMat = Matrix(((cos(zAng), -sin(zAng), 0.0), (sin(zAng), cos(zAng), 0.0), (0.0, 0.0, 1.0)))

	vec = xMat @ vec
	vec = yMat @ vec
	vec = zMat @ vec

	bpy.data.worlds['Lumiere_world'].node_tree.nodes['Sky Texture'].sun_direction = vec
	bpy.data.worlds['Lumiere_world'].node_tree.nodes['Sun normal'].outputs[0].default_value = vec
	bpy.data.worlds['Lumiere_world'].node_tree.nodes['Blackbody'].inputs[0].default_value = 4000 + (1780 * vec.z)

	if light is not None:
		mat = get_mat_name(light)

		blackbody = mat.node_tree.nodes['Blackbody']
		#4000 -> HORIZON // 5780 -> Daylight
		light.Lumiere.blackbody = 4000 + (1780 * vec.z)


# -------------------------------------------------------------------- #
def get_collection():
	"""Return the Lumiere collections"""
	addon_prefs = get_preferences()

	if addon_prefs.primary_collection in bpy.context.scene.collection.children.keys():
		primary_col = bpy.context.scene.collection.children[addon_prefs.primary_collection]

		if addon_prefs.lights_collection in primary_col.children:
			light_col = primary_col.children[addon_prefs.lights_collection]
		else:
			light_col = None
		#
		# if addon_prefs.camera_collection in primary_col.children:
		# 	camera_col = primary_col.children[addon_prefs.camera_collection]
		# else:
		# 	camera_col = None

		if addon_prefs.platform_collection in primary_col.children:
			platform_col = primary_col.children[addon_prefs.platform_collection]
		else:
			platform_col = None
	else:
		primary_col = light_col = platform_col = None

	return primary_col, light_col, platform_col

# -------------------------------------------------------------------- #
def create_collections(self, primary=None, lights=None, platform=None):
	# Create a new collection and link it to the scene.
	addon_prefs = get_preferences()
	primary_col, light_col, platform_col = get_collection()


	# Primary collection
	if addon_prefs.primary_collection not in bpy.data.collections:
		primary_col = bpy.data.collections.new(addon_prefs.primary_collection)
		bpy.context.scene.collection.children.link(primary_col)
	# else:
		# self.report({'WARNING'}, "Collection {} already exist, please change the name in the preferences.".format(addon_prefs.primary_collection))

	# Lights collection
	if addon_prefs.lights_collection not in bpy.data.collections:
		light_col = bpy.data.collections.new(addon_prefs.lights_collection)
		primary_col.children.link(light_col)
	# else:
		# self.report({'WARNING'}, "Collection {} already exist, please change the name in the preferences.".format(addon_prefs.lights_collection))

	# Platform collection
	if addon_prefs.platform_collection not in bpy.data.collections:
		platform_col = bpy.data.collections.new(addon_prefs.platform_collection)
		primary_col.children.link(platform_col)
	# else:
		# self.report({'WARNING'}, "Collection {} already exist, please change the name in the preferences.".format(addon_prefs.platform_collection))

	# Camera collection
	# if addon_prefs.camera_collection not in bpy.data.collections:
	# 	camera_col = bpy.data.collections.new(addon_prefs.camera_collection)
	# 	primary_col.children.link(camera_col)
	# else:
		# self.report({'WARNING'}, "Collection {} already exist, please change the name in the preferences.".format(addon_prefs.camera_collection))

# -------------------------------------------------------------------- #
def update_spherical_coordinate(self, context, light=None):
	"""Incline (tilt) and rotate the light around the targeted point"""

	if light is None:
		light = bpy.data.objects[self.id_data.name]

	r = light.Lumiere.range
	# θ theta is azimuthal angle, the angle of the rotation around the z-axis (aspect)
	theta = radians(light.Lumiere.rotation)
	# φ phi is the polar angle, rotated down from the positive z-axis (slope)
	phi = radians(light.Lumiere.tilt)

	light.location = cartesian_coordinates(r, theta, phi, light.Lumiere.hit)

	track  = light.location - Vector(light.Lumiere.hit)
	rotaxis = (track.to_track_quat('Z','Y'))
	light.rotation_euler = rotaxis.to_euler()

	# Update direction for range update
	light.Lumiere.direction = rotaxis @ Vector((0.0, 0.0, 1.0))

# -------------------------------------------------------------------- #
def get_package():
	""" Return the package name. """
	return os.path.basename(os.path.dirname(os.path.realpath(__file__)))

# -------------------------------------------------------------------- #
def get_preferences():
	""" Return the preferences. """
	__package__ = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
	preferences = bpy.context.preferences
	return preferences.addons[__package__].preferences

# -------------------------------------------------------------------- #
def create_2d_gizmo(self, context, type, icon_name, alpha, color, color_highlight, alpha_highlight, scale_basis, operator = None, action = None, arg = None, operation = None):
	"""Create a gizmo"""
	gizmo = self.gizmos.new(type)
	if operator is not None:
		op = gizmo.target_set_operator("lumiere." + operator)
		op.action = action
		op.arg = arg
		if operation:
			op.operation = operation
	gizmo.icon = icon_name
	gizmo.draw_options = {'BACKDROP', 'OUTLINE', 'HELPLINE'}
	gizmo.alpha = alpha
	gizmo.color = color
	gizmo.color_highlight = color_highlight
	gizmo.alpha_highlight = alpha_highlight
	gizmo.scale_basis = scale_basis
	return gizmo
