"""Smooth the car-2 interior floor: remove square pockets and Pi standoff bosses.

Run from project root:

    ./tools/squashfs-root/usr/bin/freecadcmd cad/smooth_floor.py

Reads  exports/car-1.5/enclosure_body.step  (pristine baseline)
Writes exports/car-2/enclosure_body.{FCStd,step,stl}
"""

from __future__ import annotations

import sys
from pathlib import Path

import FreeCAD as App
import Mesh
import Part

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SRC = ROOT / "exports" / "car-1.5" / "enclosure_body.step"
EXPORT = ROOT / "exports" / "car-2"

FLOOR = 7.621
CUT_TOP = 13.5
PI = [(163.6, 94.7), (163.6, 152.4), (212.1, 94.7), (212.1, 152.4)]

# Interior floor footprint (from aligned legacy body)
INT_X0 = 7.62
INT_Y0 = 7.62
INT_L = 213.4
INT_W = 213.4


def _fuse(boxes):
    shape = boxes[0]
    for b in boxes[1:]:
        shape = shape.fuse(b)
    return shape


def build_smooth_body() -> Part.Shape:
    body = Part.read(str(SRC))
    vol0 = body.Volume

    cutters = [
        # Square walled pockets (expanded 1 mm to catch thin rims)
        Part.makeBox(59.2, 49.5, CUT_TOP - FLOOR + 1.0, App.Vector(62.5, 41.3, FLOOR)),
        Part.makeBox(38.8, 66.8, CUT_TOP - FLOOR + 1.0, App.Vector(157.8, 11.7, FLOOR)),
        # Coplanar pocket-floor islands left at z = FLOOR
        Part.makeBox(60.0, 50.0, 0.8, App.Vector(62.0, 41.0, FLOOR - 0.4)),
        Part.makeBox(40.0, 68.0, 0.8, App.Vector(157.0, 11.0, FLOOR - 0.4)),
    ]

    # Pi standoff bosses above the interior floor
    for cx, cy in PI:
        cutters.append(
            Part.makeBox(
                6.5,
                6.5,
                CUT_TOP - FLOOR + 1.0,
                App.Vector(cx - 3.25, cy - 3.25, FLOOR),
            )
        )

    body = body.cut(_fuse(cutters))

    # Fill Pi through-holes so the interior floor is flat (no open bores)
    fillers = [
        Part.makeCylinder(2.0, FLOOR, App.Vector(cx, cy, 0.0), App.Vector(0, 0, 1))
        for cx, cy in PI
    ]
    body = body.fuse(_fuse(fillers))
    try:
        body = Part.refineShape(body)
    except Exception:
        pass
    body = body.removeSplitter()

    print(f"Volume {vol0:.0f} -> {body.Volume:.0f} mm³ (removed {vol0 - body.Volume:.0f})")
    return body


def save_exports(body: Part.Shape) -> None:
    EXPORT.mkdir(parents=True, exist_ok=True)
    doc = App.newDocument("enclosure_body")
    obj = doc.addObject("Part::Feature", "Body")
    obj.Shape = body
    doc.recompute()
    doc.saveAs(str(EXPORT / "enclosure_body.FCStd"))
    body.exportStep(str(EXPORT / "enclosure_body.step"))
    mesh = Mesh.Mesh()
    mesh.addFacets(body.tessellate(0.1))
    mesh.write(str(EXPORT / "enclosure_body.stl"))
    App.closeDocument(doc.Name)
    print("Wrote exports/car-2/enclosure_body.{FCStd,step,stl}")


def main() -> None:
    if not SRC.exists():
        print(f"Missing baseline: {SRC}", file=sys.stderr)
        sys.exit(1)
    save_exports(build_smooth_body())


main()
