import FreeCAD as App
import Part
import Mesh
from pathlib import Path
import math

export = Path("exports/car-2")
lid_path = export / "enclosure_lid.step"

lid = Part.read(str(lid_path))

mat = App.Matrix()
mat.rotateX(math.radians(-90))
lid.transformShape(mat)

doc = App.newDocument("enclosure_lid")
obj = doc.addObject("Part::Feature", "Lid")
obj.Shape = lid
doc.recompute()
doc.saveAs(str(export / "enclosure_lid.FCStd"))
lid.exportStep(str(lid_path))

mesh = Mesh.Mesh()
mesh.addFacets(lid.tessellate(0.1))
mesh.write(str(export / "enclosure_lid.stl"))
App.closeDocument(doc.Name)
print("Rewrote lid to Y-up")
