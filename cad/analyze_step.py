#!/usr/bin/env python3
"""Analyze STEP files: bounding box, hole radii, large faces."""
from __future__ import annotations

import sys
from pathlib import Path

import FreeCAD as App  # noqa: E402
import Part  # noqa: E402


def analyze(path: Path, label: str) -> None:
    shape = Part.read(str(path))
    bb = shape.BoundBox
    print(f"\n{'=' * 60}")
    print(f"{label}: {path.name}")
    print(f"BBox mm: {bb.XLength:.2f} x {bb.YLength:.2f} x {bb.ZLength:.2f}")
    print(f"BBox in: {bb.XLength / 25.4:.3f} x {bb.YLength / 25.4:.3f} x {bb.ZLength / 25.4:.3f}")
    print(f"Origin: X[{bb.XMin:.2f}..{bb.XMax:.2f}]  Y[{bb.YMin:.2f}..{bb.YMax:.2f}]  Z[{bb.ZMin:.2f}..{bb.ZMax:.2f}]")
    print(f"Volume: {shape.Volume:.0f} mm^3")

    radii: dict[float, list[tuple[float, float, float]]] = {}
    for f in shape.Faces:
        try:
            r = f.Surface.Radius
            if r and r > 0:
                c = f.CenterOfMass
                radii.setdefault(round(r, 3), []).append((c.x, c.y, c.z))
        except Exception:
            pass

    print("Cylindrical features by radius (mm):")
    for r in sorted(radii):
        pts = radii[r]
        print(f"  r={r:.3f}  count={len(pts)}  (D={2 * r:.3f} mm)")
        for p in pts[:5]:
            print(f"    @ ({p[0]:.2f}, {p[1]:.2f}, {p[2]:.2f})")
        if len(pts) > 5:
            print(f"    ... +{len(pts) - 5} more")

    big_faces = []
    for f in shape.Faces:
        try:
            area = f.Area
            if area > 3000:
                n = f.normalAt(0.5, 0.5)
                c = f.CenterOfMass
                big_faces.append((area, (n.x, n.y, n.z), c))
        except Exception:
            pass
    big_faces.sort(reverse=True)
    print("Largest faces:")
    for area, n, c in big_faces[:10]:
        print(f"  area={area:.0f}  n=({n[0]:.2f},{n[1]:.2f},{n[2]:.2f})  c=({c.x:.1f},{c.y:.1f},{c.z:.1f})")


def main():
    try:
        root = Path(__file__).resolve().parent.parent
    except NameError:
        root = Path.cwd().resolve()
    car15 = root / "exports" / "car-1.5"
    car2 = root / "exports" / "car-2"
    files = [
        ("CAR 1.5 SOURCE BOTTOM", car15 / "SoftwareEnclosureBottomCar1.5.STEP"),
        ("CAR 1.5 SOURCE TOP", car15 / "SoftwareEnclosureTopCar1.5.STEP"),
        ("CAR 1.5 BODY", car15 / "enclosure_body.step"),
        ("CAR 1.5 LID", car15 / "enclosure_lid.step"),
        ("CAR 2 BODY", car2 / "enclosure_body.step"),
        ("CAR 2 LID", car2 / "enclosure_lid.step"),
    ]
    for label, path in files:
        if path.exists():
            analyze(path, label)
        else:
            print(f"\nMISSING: {path}")


if __name__ == "__main__":
    main()
