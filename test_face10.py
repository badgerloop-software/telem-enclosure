import FreeCAD as App
import Part

print("--- car-1.5 ---")
shape1 = Part.read("exports/car-1.5/enclosure_body.step")
for idx in [7, 9]: # Face 8 is index 7, Face 10 is index 9
    f = shape1.Faces[idx]
    c = f.CenterOfMass
    n = f.normalAt(0.5, 0.5) if hasattr(f, 'normalAt') else None
    print(f"Face {idx+1}: Center=({c.x:.2f}, {c.y:.2f}, {c.z:.2f}) Normal={n}")

print("--- car-2 ---")
shape2 = Part.read("exports/car-2/enclosure_body.step")
for idx in [7, 9]:
    f = shape2.Faces[idx]
    c = f.CenterOfMass
    n = f.normalAt(0.5, 0.5) if hasattr(f, 'normalAt') else None
    print(f"Face {idx+1}: Center=({c.x:.2f}, {c.y:.2f}, {c.z:.2f}) Normal={n}")

