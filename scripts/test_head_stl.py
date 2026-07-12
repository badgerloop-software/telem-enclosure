from stl import mesh
m = mesh.Mesh.from_file("exports/car-2/enclosure_body_head.stl")
print("HEAD Min:", m.vectors.reshape(-1, 3).min(axis=0))
print("HEAD Max:", m.vectors.reshape(-1, 3).max(axis=0))
