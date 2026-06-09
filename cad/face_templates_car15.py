#!/usr/bin/env python3
"""
Generate 1:1 scale face-template PDF for the car-1.5 recovered enclosure.

Hole positions come from cad/params_car15.json (axis-based extraction from STEP).
Re-run extract_car15_features.py after model changes.

Output:  exports/car-1.5/face_templates.pdf
Usage:   tools/render-venv/bin/python cad/face_templates_car15.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch
from matplotlib.backends.backend_pdf import PdfPages

HERE = Path(__file__).resolve().parent
EXPORTS = HERE.parent / "exports" / "car-1.5"
PARAMS = HERE / "params_car15.json"

MARGIN_X, MARGIN_Y, HDR, FTR = 22, 18, 14, 16
WALL_FC, WALL_EC = "#DEDEDE", "#333333"
CAVITY_FC = "#FFFFFF"
CUT_FC, CUT_EC = "#FFCDD2", "#C62828"
BOSS_FC, BOSS_EC = "#BDBDBD", "#555555"
PILOT_FC, PILOT_EC = "#757575", "#222222"
DIM_C, WARN_C = "#5D4037", "#B71C1C"


def _load():
    return json.loads(PARAMS.read_text())


def _holes(data, wall):
    return data["holes_by_wall"].get(wall, [])


def _cutouts(data, wall):
    return [c for c in data.get("cutouts", []) if c["wall"] == wall]


def _r(ax, x, y, w, h, **kw):
    defaults = dict(fc=CAVITY_FC, ec=WALL_EC, lw=0.8, ls="-", alpha=1.0, zorder=2)
    defaults.update(kw)
    hatch = defaults.pop("hatch", None)
    if hatch:
        defaults["hatch"] = hatch
    ax.add_patch(Rectangle((x, y), w, h, **defaults))


def _c(ax, cx, cy, d, fc=PILOT_FC, ec=PILOT_EC, lw=0.8, zorder=4):
    ax.add_patch(Circle((cx, cy), d / 2, facecolor=fc, edgecolor=ec, linewidth=lw, zorder=zorder))


def _txt(ax, x, y, text, size=4.5, color="#333", ha="center", va="center", **kw):
    ax.text(x, y, text, fontsize=size, color=color, ha=ha, va=va, **kw)


def _dim_h(ax, x1, x2, y, label, size=4):
    ax.annotate("", xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle="<->", color=DIM_C, lw=0.55, mutation_scale=5), zorder=6)
    _txt(ax, (x1 + x2) / 2, y + 1.8, label, size=size, color=DIM_C)


def _dim_v(ax, x, y1, y2, label, size=4):
    ax.annotate("", xy=(x, y2), xytext=(x, y1),
                arrowprops=dict(arrowstyle="<->", color=DIM_C, lw=0.55, mutation_scale=5), zorder=6)
    _txt(ax, x + 2.5, (y1 + y2) / 2, label, size=size, color=DIM_C,
         rotation=90, rotation_mode="anchor", ha="left", va="center")


def _scale_bar(ax, x, y, length=30):
    ax.plot([x, x + length], [y, y], "k-", lw=1.3, zorder=7)
    _txt(ax, x + length / 2, y + 3, f"{length} mm", size=5.5)


def _draw_cutouts(ax, ox, oy, data, wall, label=None):
    for c in _cutouts(data, wall):
        uw = c["u1"] - c["u0"]
        vw = c["v1"] - c["v0"]
        _r(ax, ox + c["u0"], oy + c["v0"], uw, vw,
           fc=CUT_FC, ec=CUT_EC, lw=0.7, hatch="///", alpha=0.45, zorder=3)
        if label and c == _cutouts(data, wall)[0]:
            _txt(ax, ox + (c["u0"] + c["u1"]) / 2, oy + (c["v0"] + c["v1"]) / 2,
                 label, size=3.8, color=CUT_EC)


def _draw_holes(ax, ox, oy, holes, hole_fc=PILOT_FC, hole_ec=PILOT_EC, lw=0.8):
    for h in holes:
        d = h["d"]
        fc = CUT_FC if d > 10 else BOSS_FC if d > 5 else hole_fc
        ec = CUT_EC if d > 10 else BOSS_EC if d > 5 else hole_ec
        _c(ax, ox + h["u"], oy + h["v"], d, fc=fc, ec=ec, lw=lw)


def make_page(pdf, title, subtitle, face_w, face_h, draw_fn):
    total_w = face_w + 2 * MARGIN_X
    total_h = face_h + HDR + FTR + MARGIN_Y
    fig, ax = plt.subplots(figsize=(total_w / 25.4, total_h / 25.4))
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(0, total_w)
    ax.set_ylim(0, total_h)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.patch.set_facecolor("#FAFAFA")
    ox, oy = MARGIN_X, FTR + MARGIN_Y / 2
    draw_fn(ax, ox, oy, face_w, face_h)
    _txt(ax, total_w / 2, oy + face_h + HDR * 0.75, title, size=8.5, color="#111", fontweight="bold")
    _txt(ax, total_w / 2, oy + face_h + HDR * 0.20, subtitle, size=5, color="#555")
    _scale_bar(ax, MARGIN_X, FTR * 0.4, 30)
    _txt(ax, total_w * 0.62, FTR * 0.4,
         "⚠  PRINT AT EXACTLY 100%  ·  DISABLE 'FIT TO PAGE'  ·  ALL DIMS IN mm",
         size=5, color=WARN_C, ha="center")
    pdf.savefig(fig)
    plt.close(fig)


def draw_floor(ax, ox, oy, fw, fh, data):
    wt = data.get("wall_t", 7.6)
    _r(ax, ox, oy, fw, fh, fc=WALL_FC, ec=WALL_EC, lw=1.2)
    _r(ax, ox + wt, oy + wt, fw - 2 * wt, fh - 2 * wt, fc=CAVITY_FC, ec="#888", lw=0.6)
    _draw_holes(ax, ox, oy, _holes(data, "floor"))
    _r(ax, ox, oy, fw, fh, fc="none", ec=WALL_EC, lw=1.2)
    _dim_h(ax, ox, ox + fw, oy - 7, f"{fw:.0f}")
    _dim_v(ax, ox + fw + 7, oy, oy + fh, f"{fh:.0f}")
    n = len(_holes(data, "floor"))
    _txt(ax, ox + fw / 2, oy - 12, f"↑  FRONT (Y=0)  |  {n}× floor-mount holes", size=4.5, color="#777")


def draw_left_wall(ax, ox, oy, fw, fh, data):
    _r(ax, ox, oy, fw, fh, fc=WALL_FC, ec=WALL_EC, lw=1.2)
    holes = _holes(data, "left")
    _draw_holes(ax, ox, oy, holes)
    _draw_cutouts(ax, ox, oy, data, "left")
    # Label large holes
    for h in holes:
        if h["d"] > 15:
            _txt(ax, ox + h["u"], oy + h["v"], f"D={h['d']:.0f}", size=3.5, color=CUT_EC)
    if len(holes) >= 2:
        by_d = {}
        for h in holes:
            by_d.setdefault(h["d"], []).append(h)
        for d, grp in by_d.items():
            if len(grp) >= 2 and d > 15:
                grp = sorted(grp, key=lambda x: x["v"])
                _dim_v(ax, ox + grp[0]["u"] + 12, oy + grp[0]["v"], oy + grp[-1]["v"],
                       f"{grp[-1]['v'] - grp[0]['v']:.1f}", size=3.5)
    _r(ax, ox, oy, fw, fh, fc="none", ec=WALL_EC, lw=1.2)
    _dim_h(ax, ox, ox + fw, oy - 6, f"{fw:.0f}")
    _dim_v(ax, ox + fw + 6, oy, oy + fh, f"{fh:.0f}")
    _txt(ax, ox + fw / 2, oy - 11, f"LEFT WALL  |  {len(holes)} holes", size=4.5, color="#777")


def draw_right_wall(ax, ox, oy, fw, fh, data):
    _r(ax, ox, oy, fw, fh, fc=WALL_FC, ec=WALL_EC, lw=1.2)
    holes = _holes(data, "right")
    _draw_holes(ax, ox, oy, holes, lw=0.5)
    _draw_cutouts(ax, ox, oy, data, "right", "I/O cutout")
    vents = [h for h in holes if h["d"] < 6]
    _txt(ax, ox + 55, oy + 20, f"Vent holes: {len(vents)}× D≈5.1", size=3.8, color=CUT_EC)
    _r(ax, ox, oy, fw, fh, fc="none", ec=WALL_EC, lw=1.2)
    _dim_h(ax, ox, ox + fw, oy - 6, f"{fw:.0f}")
    _dim_v(ax, ox + fw + 6, oy, oy + fh, f"{fh:.0f}")
    _txt(ax, ox + fw / 2, oy - 11, f"RIGHT WALL  |  {len(holes)} holes", size=4.5, color="#777")


def draw_front_wall(ax, ox, oy, fw, fh, data):
    _r(ax, ox, oy, fw, fh, fc=WALL_FC, ec=WALL_EC, lw=1.2)
    holes = _holes(data, "front")
    _draw_holes(ax, ox, oy, holes)
    _draw_cutouts(ax, ox, oy, data, "front", "media cutout")
    if len(holes) >= 2:
        xs = sorted(h["u"] for h in holes)
        _dim_h(ax, ox + xs[0], ox + xs[-1], oy + fh + 5, f"{xs[-1] - xs[0]:.0f}", size=3.5)
    _r(ax, ox, oy, fw, fh, fc="none", ec=WALL_EC, lw=1.2)
    _dim_h(ax, ox, ox + fw, oy - 6, f"{fw:.0f}")
    _dim_v(ax, ox + fw + 6, oy, oy + fh, f"{fh:.0f}")
    _txt(ax, ox + fw / 2, oy - 11, f"FRONT WALL  |  {len(holes)} holes", size=4.5, color="#777")


def draw_back_wall(ax, ox, oy, fw, fh, data):
    _r(ax, ox, oy, fw, fh, fc=WALL_FC, ec=WALL_EC, lw=1.2)
    holes = _holes(data, "back")
    _draw_holes(ax, ox, oy, holes)
    _draw_cutouts(ax, ox, oy, data, "back")
    # Antenna column label
    ant = [h for h in holes if h["d"] < 8]
    if len(ant) >= 2:
        ant = sorted(ant, key=lambda x: x["v"])
        _dim_v(ax, ox + ant[0]["u"] + 10, oy + ant[0]["v"], oy + ant[-1]["v"],
               f"{ant[-1]['v'] - ant[0]['v']:.0f}", size=3.5)
        _txt(ax, ox + ant[0]["u"] + 12, oy + (ant[0]["v"] + ant[-1]["v"]) / 2,
             "antenna", size=4, color=CUT_EC, ha="left")
    _r(ax, ox, oy, fw, fh, fc="none", ec=WALL_EC, lw=1.2)
    _dim_h(ax, ox, ox + fw, oy - 6, f"{fw:.0f}")
    _dim_v(ax, ox + fw + 6, oy, oy + fh, f"{fh:.0f}")
    _txt(ax, ox + fw / 2, oy - 11, f"BACK WALL (interior face)  |  {len(holes)} holes", size=4.5, color="#777")


def draw_lid(ax, ox, oy, fw, fh, data):
    _r(ax, ox, oy, fw, fh, fc=WALL_FC, ec=WALL_EC, lw=1.2)
    for h in data.get("lid_holes", []):
        _c(ax, ox + h["u"], oy + h["v"], h["d"], fc=CUT_FC, ec=CUT_EC, lw=0.8)
    n = len(data.get("lid_holes", []))
    _txt(ax, ox + fw / 2, oy + fh / 2, f"Lid screw clearance\n{n}× D≈4.1 mm", size=5, color=CUT_EC)
    _r(ax, ox, oy, fw, fh, fc="none", ec=WALL_EC, lw=1.2)
    _dim_h(ax, ox, ox + fw, oy - 6, f"{fw:.0f}")
    _dim_v(ax, ox + fw + 6, oy, oy + fh, f"{fh:.0f}")


def main():
    if not PARAMS.exists():
        raise FileNotFoundError("Run extract_car15_features.py first.")
    data = _load()
    EXPORTS.mkdir(parents=True, exist_ok=True)
    out = EXPORTS / "face_templates.pdf"

    ext_l, ext_w, body_h = data["ext_l"], data["ext_w"], data["body_h"]
    pages = [
        ("FLOOR PLAN  ·  car-1.5",
         f"{ext_l:.0f}×{ext_w:.0f} mm  |  floor-mount holes from STEP geometry",
         ext_l, ext_w, lambda ax, ox, oy, fw, fh: draw_floor(ax, ox, oy, fw, fh, data)),
        ("LEFT SHORT WALL",
         f"{len(_holes(data,'left'))} holes  |  axis-classified from STEP",
         ext_w, body_h, lambda ax, ox, oy, fw, fh: draw_left_wall(ax, ox, oy, fw, fh, data)),
        ("RIGHT SHORT WALL",
         f"{len(_holes(data,'right'))} holes  |  vent grid + I/O cutout",
         ext_w, body_h, lambda ax, ox, oy, fw, fh: draw_right_wall(ax, ox, oy, fw, fh, data)),
        ("FRONT LONG WALL",
         f"{len(_holes(data,'front'))} holes  |  media / large ports",
         ext_l, body_h, lambda ax, ox, oy, fw, fh: draw_front_wall(ax, ox, oy, fw, fh, data)),
        ("BACK LONG WALL — INTERIOR FACE",
         f"{len(_holes(data,'back'))} holes  |  antenna stack",
         ext_l, body_h, lambda ax, ox, oy, fw, fh: draw_back_wall(ax, ox, oy, fw, fh, data)),
        ("LID  ·  top view",
         f"{len(data.get('lid_holes',[]))} corner screw holes",
         ext_l, ext_w, lambda ax, ox, oy, fw, fh: draw_lid(ax, ox, oy, fw, fh, data)),
    ]

    with PdfPages(out) as pdf:
        for title, subtitle, fw, fh, fn in pages:
            make_page(pdf, title, subtitle, fw, fh, fn)

    print(f"Saved {out}  ({out.stat().st_size // 1024} KB, {len(pages)} pages)")
    print("Hole counts:", data.get("hole_count", {}))


if __name__ == "__main__":
    main()
