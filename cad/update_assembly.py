"""Rebuild telem_enclosure_assembly.FCStd from current body + lid STEP files.

Run from project root:

    ./tools/squashfs-root/usr/bin/freecadcmd cad/update_assembly.py [car-1.5|car-2]
"""

from __future__ import annotations

import sys
from pathlib import Path

import FreeCAD as App
import Part

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def update_assembly(version: str = "car-2") -> None:
    export = ROOT / "exports" / version
    body_path = export / "enclosure_body.step"
    lid_path = export / "enclosure_lid.step"
    if not body_path.exists() or not lid_path.exists():
        raise FileNotFoundError(f"Missing body or lid STEP in {export}")

    body = Part.read(str(body_path))
    lid_raw = Part.read(str(lid_path))
    
    # Body is already rotated to Y-up by smooth_floor.py.
    # Lid comes from car-1.5 which is Z-up, so we must rotate it to match!
    import math
    mat = App.Matrix()
    mat.rotateX(math.radians(-90))
    lid = lid_raw.copy()
    lid.transformShape(mat)
    
    body_h = body.BoundBox.YMax
    lid_placed = lid.copy()
    lid_placed.translate(App.Vector(0, body_h, 0))

    asm = App.newDocument("telem_enclosure_assembly")
    body_a = asm.addObject("Part::Feature", "Body")
    body_a.Shape = body
    lid_a = asm.addObject("Part::Feature", "Lid")
    lid_a.Shape = lid_placed
    asm.recompute()
    out = export / "telem_enclosure_assembly.FCStd"
    asm.saveAs(str(out))
    App.closeDocument(asm.Name)
    print(f"Wrote {out}")
    
    combined = body.fuse(lid_placed)
    out_stl = export / "telem_enclosure_assembly.stl"
    combined.exportStl(str(out_stl))
    print(f"Wrote {out_stl}")


def main() -> None:
    version = "car-2"
    for arg in sys.argv[1:]:
        if arg in {"car-1.5", "car-2"}:
            version = arg
            break
    update_assembly(version)


main()
