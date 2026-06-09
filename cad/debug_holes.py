#!/usr/bin/env python3
import math
from collections import defaultdict
from pathlib import Path
import Part

try:
    _root = Path(__file__).resolve().parent.parent
except NameError:
    _root = Path.cwd().resolve()
body = Part.read(str(_root / "exports/car-1.5/enclosure_body.step"))
bb = body.BoundBox
print(f"BBox: {bb.XLength} x {bb.YLength} x {bb.ZLength}")

by_dom = defaultdict(list)
for face in body.Faces:
    try:
        s = face.Surface
        if not hasattr(s, "Radius"):
            continue
        r = s.Radius
        if not r or r < 0.5:
            continue
        axis = s.Axis
        c = face.CenterOfMass
        ax, ay, az = axis.x, axis.y, axis.z
        al = math.sqrt(ax * ax + ay * ay + az * az)
        if al < 1e-9:
            continue
        ax, ay, az = ax / al, ay / al, az / al
        dom = ("x" if abs(ax) > 0.85 else
               "y" if abs(ay) > 0.85 else
               "z" if abs(az) > 0.85 else "?")
        by_dom[f"{dom}_D{2*r:.2f}"].append((round(c.x, 1), round(c.y, 1), round(c.z, 1)))
    except Exception:
        pass

for k in sorted(by_dom):
    pts = by_dom[k]
    print(f"{k}: {len(pts)} unique-ish")
    # dedupe
    ded = []
    for p in pts:
        if not any(all(abs(p[i]-o[i])<1.5 for i in range(3)) for o in ded):
            ded.append(p)
    for p in ded[:12]:
        print(f"    {p}")
    if len(ded) > 12:
        print(f"    ...+{len(ded)-12} more (deduped total {len(ded)})")
