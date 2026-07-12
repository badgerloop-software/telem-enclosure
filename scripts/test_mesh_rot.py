import FreeCAD as App
import Part
import Mesh
import math

b = Part.makeBox(10, 10, 10)
m = Mesh.Mesh()
m.addFacets(b.tessellate(0.1))
mat = App.Matrix()
mat.rotateX(math.radians(-90))
m.transform(mat)
print(m.BoundBox)
