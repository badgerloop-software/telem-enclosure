#!/usr/bin/env python3
"""Import recovered SolidWorks STEP files as the enclosure baseline.

Loads SoftwareEnclosureBottomCar1.5.STEP and SoftwareEnclosureTopCar1.5.STEP
from the project root, translates the bottom part so both share a common
origin (0,0,0) at the outer bottom-front-left corner, then exports:

    exports/car-1.5/enclosure_body.{FCStd,step,stl}
    exports/car-1.5/enclosure_lid.{FCStd,step,stl}
    exports/car-1.5/telem_enclosure_assembly.FCStd

Run from project root:
    freecadcmd cad/import_legacy.py
    # or:
    echo 'exec(open("cad/import_legacy.py").read())' | \\
      ./tools/squashfs-root/usr/bin/freecadcmd
"""
from __future__ import annotations

import sys
from pathlib import Path

import FreeCAD as App
import Part
import Mesh

try:
    HERE = Path(__file__).resolve().parent
except NameError:
    cwd = Path.cwd().resolve()
    HERE = cwd / "cad" if (cwd / "cad").is_dir() else cwd

ROOT = HERE.parent
EXPORT_DIR = ROOT / "exports" / "car-1.5"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

LEGACY_BOTTOM = EXPORT_DIR / "SoftwareEnclosureBottomCar1.5.STEP"
LEGACY_TOP = EXPORT_DIR / "SoftwareEnclosureTopCar1.5.STEP"


def _save_step(shape: Part.Shape, path: Path) -> None:
    shape.exportStep(str(path))


def _save_stl(shape: Part.Shape, path: Path) -> None:
    m = Mesh.Mesh()
    m.addFacets(shape.tessellate(0.1))
    m.write(str(path))


def _align_bottom(shape: Part.Shape) -> Part.Shape:
    """Shift bottom so outer bbox starts at (0, 0, 0), matching the lid frame."""
    bb = shape.BoundBox
    aligned = shape.copy()
    aligned.translate(App.Vector(-bb.XMin, -bb.YMin, -bb.ZMin))
    return aligned


def _report(label: str, shape: Part.Shape) -> None:
    bb = shape.BoundBox
    print(f"\n{label}")
    print(f"  Extents: {bb.XLength:.2f} × {bb.YLength:.2f} × {bb.ZLength:.2f} mm")
    print(f"  Origin:  X[{bb.XMin:.2f}..{bb.XMax:.2f}]  "
          f"Y[{bb.YMin:.2f}..{bb.YMax:.2f}]  "
          f"Z[{bb.ZMin:.2f}..{bb.ZMax:.2f}]")


def main() -> None:
    if not LEGACY_BOTTOM.exists():
        raise FileNotFoundError(f"Missing legacy bottom: {LEGACY_BOTTOM}")
    if not LEGACY_TOP.exists():
        raise FileNotFoundError(f"Missing legacy top: {LEGACY_TOP}")

    print("Importing recovered SolidWorks STEP files …")
    bottom_raw = Part.read(str(LEGACY_BOTTOM))
    lid_raw = Part.read(str(LEGACY_TOP))

    body = _align_bottom(bottom_raw)
    lid = lid_raw.copy()
    # Lid Z frame: outer top at Z=LID thickness, lip hangs below Z=0.
    # Shift so outer bottom of lid plate sits at Z = BODY_H when assembled.
    body_h = body.BoundBox.ZMax
    lid_placed = lid.copy()
    lid_placed.translate(App.Vector(0, 0, body_h))

    _report("Body (aligned)", body)
    _report("Lid", lid)
    _report("Lid (placed on body)", lid_placed)

    # ---- Body document ----
    body_doc = App.newDocument("enclosure_body")
    body_obj = body_doc.addObject("Part::Feature", "Body")
    body_obj.Shape = body
    body_doc.recompute()
    body_doc.saveAs(str(EXPORT_DIR / "enclosure_body.FCStd"))
    _save_step(body, EXPORT_DIR / "enclosure_body.step")
    _save_stl(body, EXPORT_DIR / "enclosure_body.stl")
    App.closeDocument(body_doc.Name)

    # ---- Lid document ----
    lid_doc = App.newDocument("enclosure_lid")
    lid_obj = lid_doc.addObject("Part::Feature", "Lid")
    lid_obj.Shape = lid
    lid_doc.recompute()
    lid_doc.saveAs(str(EXPORT_DIR / "enclosure_lid.FCStd"))
    _save_step(lid, EXPORT_DIR / "enclosure_lid.step")
    _save_stl(lid, EXPORT_DIR / "enclosure_lid.stl")
    App.closeDocument(lid_doc.Name)

    # ---- Assembly preview ----
    asm = App.newDocument("telem_enclosure_assembly")
    body_a = asm.addObject("Part::Feature", "Body")
    body_a.Shape = body
    lid_a = asm.addObject("Part::Feature", "Lid")
    lid_a.Shape = lid_placed
    asm.recompute()
    asm.saveAs(str(EXPORT_DIR / "telem_enclosure_assembly.FCStd"))
    App.closeDocument(asm.Name)

    print("\nWrote outputs to:", EXPORT_DIR)
    for p in sorted(EXPORT_DIR.iterdir()):
        if p.suffix.lower() in {".fcstd", ".step", ".stl"}:
            print(f"  {p.name}  ({p.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
