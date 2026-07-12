import FreeCAD as App
import Part
p = Part.read("exports/car-2/enclosure_body.step")
print(p.BoundBox)
