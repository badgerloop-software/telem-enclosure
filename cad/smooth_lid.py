"""Modify the car-1.5 lid to fit the car-2 body.

Run from project root:
    ./tools/squashfs-root/usr/bin/freecadcmd cad/smooth_lid.py
"""

import sys
from pathlib import Path

import FreeCAD as App
import Part

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SRC = ROOT / "exports" / "car-1.5" / "enclosure_lid.step"
EXPORT = ROOT / "exports" / "car-2"

def _fuse(shapes):
    if not shapes:
        return None
    res = shapes[0]
    for s in shapes[1:]:
        res = res.fuse(s)
    return res

print(f"Loading {SRC}")
shape = Part.read(str(SRC))
body = shape

# 1. Cut away the deep portion of the L-shape (Y > 101.6)
# The lid spans X=[0, 228.6]. Cut everything Y > 101.6
cut_box = Part.makeBox(250, 150, 20, App.Vector(-10, 101.6, -10))
body = body.cut(cut_box)

# 2. Cut the inner lip on the right side to match the new thin wall.
# The new thin wall on the body right half starts at Y=99.06.
# The inner lip of the lid (Z < 0) currently extends to Y=101.6 after the first cut.
# We must trim the lip for Y=[99.06, 101.6] on the right half (X > 134.62).
lip_cut = Part.makeBox(
    100,            # X width (134.62 to 230)
    10,             # Y depth (99.06 to 109.06)
    10,             # Z height (Z=-10 to Z=0.0) -> This removes only the lip, not the top flange
    App.Vector(134.62, 99.06, -10)
)
body = body.cut(lip_cut)

# 3. Drill the 4 corner screw holes to perfectly match the body holes.
# Body holes are at X in {3.81, 224.79}, Y in {3.81, 97.79}.
LID_HOLE_R = 2.54  # Clearance hole
holes = []
for x in [3.81, 224.79]:
    for y in [3.81, 97.79]:
        holes.append(Part.makeCylinder(LID_HOLE_R, 20, App.Vector(x, y, -10), App.Vector(0, 0, 1)))

body = body.cut(_fuse(holes))

try:
    body = Part.refineShape(body)
except Exception:
    pass
body = body.removeSplitter()

EXPORT.mkdir(parents=True, exist_ok=True)
out_step = EXPORT / "enclosure_lid.step"
out_stl = EXPORT / "enclosure_lid.stl"
out_fcstd = EXPORT / "enclosure_lid.FCStd"

print(f"Writing {out_step}")
body.exportStep(str(out_step))
body.exportStl(str(out_stl))

doc = App.newDocument("Lid")
obj = doc.addObject("Part::Feature", "Lid")
obj.Shape = body
doc.saveAs(str(out_fcstd))
print("Done lid!")
