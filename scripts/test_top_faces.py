import FreeCAD as App
import Part

body = Part.read("exports/car-1.5/enclosure_body.step")
z_vals = set()
for f in body.Faces:
    bb = f.BoundBox
    if bb.ZMin > 45:
        z_vals.add(round(bb.ZMin, 2))
        z_vals.add(round(bb.ZMax, 2))
print("High Z values:", sorted(list(z_vals)))
