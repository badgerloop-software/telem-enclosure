import trimesh
mesh = trimesh.load("exports/car-2/enclosure_body.stl")
print("Bounds:", mesh.bounds)
print("Center:", mesh.centroid)
