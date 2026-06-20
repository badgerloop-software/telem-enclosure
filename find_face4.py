import FreeCAD as App
import Part

shape = Part.read("exports/car-2/enclosure_body.step")
f = shape.Faces[3]  # Face4 is index 3
print(f"Face 4: Center={f.CenterOfMass}, Normal={f.normalAt(0.5, 0.5) if hasattr(f, 'normalAt') else None}")
