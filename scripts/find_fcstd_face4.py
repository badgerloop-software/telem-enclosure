import FreeCAD as App
import Part

doc = App.openDocument("exports/car-2/enclosure_body.FCStd")
obj = doc.getObject("Body")
f = obj.Shape.Faces[3]  # Face4 is 1-based, so index 3
print(f"Face 4 of FCStd Body: Center={f.CenterOfMass}, Normal={f.normalAt(0.5, 0.5) if hasattr(f, 'normalAt') else None}")
