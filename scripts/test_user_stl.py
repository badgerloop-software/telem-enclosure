from stl import mesh
import numpy as np
m = mesh.Mesh.from_file("exports/car-2/enclosure_body.stl")
print("Min:", m.vectors.reshape(-1, 3).min(axis=0))
print("Max:", m.vectors.reshape(-1, 3).max(axis=0))
