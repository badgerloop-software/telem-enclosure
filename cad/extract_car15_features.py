#!/usr/bin/env python3
"""Extract wall features from car-1.5 STEP for face-template generation.

Classifies holes by cylinder AXIS direction first, then snaps to the nearest
exterior wall plane.  Interior/divider holes (e.g. X≈136 shelf posts) are
excluded from exterior-face templates.
"""
from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

import FreeCAD as App  # noqa: E402
import Part  # noqa: E402

try:
    ROOT = Path(__file__).resolve().parent.parent
except NameError:
    ROOT = Path.cwd().resolve()

CAR15 = ROOT / "exports" / "car-1.5"
BODY_PATH = CAR15 / "enclosure_body.step"
LID_PATH = CAR15 / "enclosure_lid.step"

WALL_NEAR = 12.0   # mm from exterior plane to count as a wall hole
FLOOR_NEAR = 6.0   # floor mounts sit near Z=0; bosses at Z≈10 are interior
DEDUPE_TOL = 2.5   # merge inner/outer cylindrical face pairs (not separate holes)


def _cyl(face):
    try:
        s = face.Surface
        if not hasattr(s, "Radius") or not s.Radius or s.Radius < 0.5:
            return None
        ax, ay, az = s.Axis.x, s.Axis.y, s.Axis.z
        al = math.sqrt(ax * ax + ay * ay + az * az)
        if al < 1e-9:
            return None
        c = face.CenterOfMass
        return {
            "cx": c.x, "cy": c.y, "cz": c.z,
            "ax": ax / al, "ay": ay / al, "az": az / al,
            "d": round(2 * s.Radius, 2),
        }
    except Exception:
        return None


def _wall_for(h, ext_l, ext_w, body_h):
    """Return (wall_name, u, v) or None if interior/non-exterior."""
    cx, cy, cz = h["cx"], h["cy"], h["cz"]
    ax, ay, az = h["ax"], h["ay"], h["az"]

    if abs(ax) > 0.85:
        if cx < WALL_NEAR:
            return "left", cy, cz
        if cx > ext_l - WALL_NEAR:
            return "right", cy, cz
        return None  # interior divider (~X=136)

    if abs(ay) > 0.85:
        if cy < WALL_NEAR:
            return "front", cx, cz
        if cy > ext_w - WALL_NEAR:
            return "back", cx, cz
        return None

    if abs(az) > 0.85:
        if cz < FLOOR_NEAR:
            return "floor", cx, cy
        if cz > body_h - 5:
            return "top", cx, cy
        return None  # interior standoffs (Z≈10) — not exterior floor mounts

    return None


def _dedupe_holes(holes):
    """Merge duplicate cylindrical-face detections of the same physical hole."""
    out = []
    for h in holes:
        merged = False
        for i, o in enumerate(out):
            if h["wall"] != o["wall"] or abs(h["d"] - o["d"]) > 0.6:
                continue
            du = abs(h["u"] - o["u"])
            dv = abs(h["v"] - o["v"])
            # Through-wall pairs (antenna on back face): same v, u within wall thickness
            if h["wall"] == "back" and dv < 1.5 and du < WALL_NEAR:
                out[i] = {"wall": h["wall"],
                          "u": round((h["u"] + o["u"]) / 2, 2),
                          "v": round((h["v"] + o["v"]) / 2, 2),
                          "d": h["d"]}
                merged = True
                break
            # Coaxial bore inner/outer faces: very close centre
            if du < DEDUPE_TOL and dv < DEDUPE_TOL:
                merged = True
                break
        if not merged:
            out.append(h)
    return out


def _extract_holes(shape, ext_l, ext_w, body_h):
    raw = []
    for face in shape.Faces:
        h = _cyl(face)
        if not h:
            continue
        w = _wall_for(h, ext_l, ext_w, body_h)
        if not w:
            continue
        wall, u, v = w
        raw.append({"wall": wall, "u": round(u, 2), "v": round(v, 2), "d": h["d"]})
    return _dedupe_holes(raw)


def _wall_cutouts(shape, ext_l, ext_w, body_h):
    """Opening faces on exterior walls (exclude full-wall flat faces)."""
    cuts = []
    for face in shape.Faces:
        try:
            if face.Area < 600:
                continue
            n = face.normalAt(0.5, 0.5)
            bb = face.BoundBox
            if abs(n.x) > 0.9:
                wall = "left" if n.x < 0 else "right"
                span_u, span_v = bb.YLength, bb.ZLength
                u0, u1, v0, v1 = bb.YMin, bb.YMax, bb.ZMin, bb.ZMax
                full = ext_w * body_h
            elif abs(n.y) > 0.9:
                wall = "front" if n.y < 0 else "back"
                span_u, span_v = bb.XLength, bb.ZLength
                u0, u1, v0, v1 = bb.XMin, bb.XMax, bb.ZMin, bb.ZMax
                full = ext_l * body_h
            else:
                continue
            if span_u * span_v > full * 0.75:
                continue  # entire wall face, not a cutout
            cuts.append({
                "wall": wall,
                "u0": round(u0, 1), "u1": round(u1, 1),
                "v0": round(v0, 1), "v1": round(v1, 1),
                "area": round(face.Area, 0),
            })
        except Exception:
            pass
    cuts.sort(key=lambda x: -x["area"])
    # dedupe overlapping cutouts on same wall
    out = []
    for c in cuts:
        if any(c["wall"] == o["wall"]
               and abs(c["u0"] - o["u0"]) < 3 and abs(c["v0"] - o["v0"]) < 3
               for o in out):
            continue
        out.append(c)
    return out


def _extract_lid_holes(shape):
    ext_l = shape.BoundBox.XLength
    ext_w = shape.BoundBox.YLength
    body_h = shape.BoundBox.ZLength
    holes = _extract_holes(shape, ext_l, ext_w, body_h)
    # Lid holes are axis-along-Z; after import they register as floor or top.
    # Keep near-corner holes only.
    pts = [h for h in holes if h["wall"] in ("floor", "top")]
    return [{"u": h["u"], "v": h["v"], "d": h["d"]} for h in pts]


def main():
    body = Part.read(str(BODY_PATH))
    lid = Part.read(str(LID_PATH))
    bb = body.BoundBox
    ext_l, ext_w, body_h = bb.XLength, bb.YLength, bb.ZLength

    holes = _extract_holes(body, ext_l, ext_w, body_h)
    by_wall = defaultdict(list)
    for h in holes:
        by_wall[h["wall"]].append({"u": h["u"], "v": h["v"], "d": h["d"]})

    data = {
        "ext_l": round(ext_l, 2),
        "ext_w": round(ext_w, 2),
        "body_h": round(body_h, 2),
        "lid_h": round(lid.BoundBox.ZLength, 2),
        "wall_t": 7.6,
        "holes_by_wall": dict(by_wall),
        "cutouts": _wall_cutouts(body, ext_l, ext_w, body_h),
        "lid_holes": _extract_lid_holes(lid),
        "hole_count": {w: len(v) for w, v in sorted(by_wall.items())},
    }

    out = ROOT / "cad" / "params_car15.json"
    out.write_text(json.dumps(data, indent=2))
    print(f"Wrote {out}")
    print("Hole counts:", data["hole_count"])
    for wall in sorted(by_wall):
        print(f"  {wall}:")
        for p in by_wall[wall]:
            print(f"    ({p['u']}, {p['v']}) D={p['d']}")


if __name__ == "__main__":
    main()
