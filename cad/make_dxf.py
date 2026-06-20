import sys
from pathlib import Path

import FreeCAD as App
import Part
import importDXF

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
EXPORT = ROOT / "exports" / "car-2"

EXPORT.mkdir(parents=True, exist_ok=True)
out_dxf = EXPORT / "enclosure_lid_flat.dxf"

# Outline: 228.6 x 101.6
outline = Part.makePlane(228.6, 101.6)

# Holes at: (3.81, 3.81), (224.79, 3.81), (3.81, 97.79), (224.79, 97.79)
LID_HOLE_R = 2.54
holes = []
for x in [3.81, 224.79]:
    for y in [3.81, 97.79]:
        circle = Part.makeCircle(LID_HOLE_R, App.Vector(x, y, 0), App.Vector(0, 0, 1))
        face = Part.Face(Part.Wire(circle))
        holes.append(face)

flat_lid = outline
for h in holes:
    flat_lid = flat_lid.cut(h)

doc = App.newDocument("DXF_Export")
obj = doc.addObject("Part::Feature", "FlatLid")
obj.Shape = flat_lid

importDXF.export([obj], str(out_dxf))
print(f"Wrote {out_dxf}")
