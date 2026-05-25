#!/usr/bin/env python3
"""
Generate a 1:1 scale face-template PDF for the telemetry enclosure.

Print at EXACTLY 100% (disable "fit to page" / "shrink to margins").
Cut out each face rectangle with scissors, then lay your components on top
to verify hole positions and cutout sizes before printing the 3D model.

Output:  exports/face_templates.pdf   (5 pages)
Usage:   tools/render-venv/bin/python cad/face_templates.py
"""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import params as P  # noqa: E402

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch
from matplotlib.backends.backend_pdf import PdfPages

EXPORTS = HERE.parent / "exports"

# ── Page layout (all mm) ─────────────────────────────────────────────────────
MARGIN_X = 22   # left/right padding around face on page
MARGIN_Y = 18   # bottom padding
HDR      = 14   # title bar height above face
FTR      = 16   # footer height below face (scale bar + warning)


# ── Colour / style constants ──────────────────────────────────────────────────
WALL_FC   = "#DEDEDE"   # wall cross-section fill
WALL_EC   = "#333333"
CAVITY_FC = "#FFFFFF"   # interior cavity
COMP_FC   = "none"      # component outline (transparent fill)
COMP_EC   = "#1565C0"   # component outline colour (dashed blue)
CUT_FC    = "#FFCDD2"   # hole / cutout fill
CUT_EC    = "#C62828"   # hole / cutout edge
BOSS_FC   = "#BDBDBD"   # standoff / boss outer ring
BOSS_EC   = "#555555"
PILOT_FC  = "#757575"   # pilot hole fill
PILOT_EC  = "#222222"
DIM_C     = "#5D4037"   # dimension line colour
WARN_C    = "#B71C1C"   # print-warning text


# ── Low-level drawing helpers ─────────────────────────────────────────────────

def _r(ax, x, y, w, h, fc=CAVITY_FC, ec=WALL_EC, lw=0.8,
       ls='-', alpha=1.0, hatch=None, zorder=2):
    kw = dict(facecolor=fc, edgecolor=ec, linewidth=lw,
              linestyle=ls, alpha=alpha, zorder=zorder)
    if hatch:
        kw['hatch'] = hatch
    ax.add_patch(Rectangle((x, y), w, h, **kw))


def _c(ax, cx, cy, d, fc=PILOT_FC, ec=PILOT_EC, lw=0.8, zorder=4):
    ax.add_patch(Circle((cx, cy), d / 2,
                        facecolor=fc, edgecolor=ec, linewidth=lw, zorder=zorder))


def _txt(ax, x, y, text, size=4.5, color='#333', ha='center', va='center', **kw):
    ax.text(x, y, text, fontsize=size, color=color, ha=ha, va=va, **kw)


def _dim_h(ax, x1, x2, y, label, arm=2.5, size=4):
    """Horizontal dimension line with end ticks and centred label."""
    ax.annotate('', xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle='<->', color=DIM_C, lw=0.55,
                                mutation_scale=5), zorder=6)
    for xp in (x1, x2):
        ax.plot([xp, xp], [y - arm / 2, y + arm / 2], color=DIM_C, lw=0.55, zorder=6)
    _txt(ax, (x1 + x2) / 2, y + 1.8, label, size=size, color=DIM_C)


def _dim_v(ax, x, y1, y2, label, arm=2.5, size=4):
    """Vertical dimension line with end ticks and rotated label."""
    ax.annotate('', xy=(x, y2), xytext=(x, y1),
                arrowprops=dict(arrowstyle='<->', color=DIM_C, lw=0.55,
                                mutation_scale=5), zorder=6)
    for yp in (y1, y2):
        ax.plot([x - arm / 2, x + arm / 2], [yp, yp], color=DIM_C, lw=0.55, zorder=6)
    _txt(ax, x + 2.5, (y1 + y2) / 2, label, size=size, color=DIM_C,
         rotation=90, rotation_mode='anchor', ha='left', va='center')


def _scale_bar(ax, x, y, length=30):
    ax.plot([x, x + length], [y, y], 'k-', lw=1.3, zorder=7)
    for xp in (x, x + length):
        ax.plot([xp, xp], [y - 2, y + 2], 'k-', lw=1.0, zorder=7)
    _txt(ax, x + length / 2, y + 3, f'{length} mm', size=5.5)


# ── Page builder ──────────────────────────────────────────────────────────────

def make_page(pdf, title, subtitle, face_w, face_h, draw_fn):
    """Render one page.  1 data unit == 1 mm when printed at 100%."""
    total_w = face_w + 2 * MARGIN_X
    total_h = face_h + HDR + FTR + MARGIN_Y

    fig, ax = plt.subplots(figsize=(total_w / 25.4, total_h / 25.4))
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_xlim(0, total_w)
    ax.set_ylim(0, total_h)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    # Background + thin page border
    fig.patch.set_facecolor('#FAFAFA')
    ax.add_patch(FancyBboxPatch((0.5, 0.5), total_w - 1, total_h - 1,
                                boxstyle="square,pad=0",
                                edgecolor='#BBBBBB', facecolor='none', lw=0.4, zorder=0))

    # Face origin (bottom-left corner of the face rectangle on page)
    ox = MARGIN_X
    oy = FTR + MARGIN_Y / 2

    draw_fn(ax, ox, oy, face_w, face_h)

    # Header
    _txt(ax, total_w / 2, oy + face_h + HDR * 0.75, title,
         size=8.5, color='#111', fontweight='bold')
    _txt(ax, total_w / 2, oy + face_h + HDR * 0.20, subtitle, size=5, color='#555')

    # Footer: scale bar left, warning centre-right
    _scale_bar(ax, MARGIN_X, FTR * 0.4, 30)
    _txt(ax, total_w * 0.62, FTR * 0.4,
         "⚠  PRINT AT EXACTLY 100%  ·  DISABLE 'FIT TO PAGE'  ·  ALL DIMS IN mm",
         size=5, color=WARN_C, ha='center')

    pdf.savefig(fig)
    plt.close(fig)


# ── PAGE 1: Floor plan ────────────────────────────────────────────────────────
# Top-down view: h = X_ext (left wall → right wall), v = Y_ext (front → back)

def draw_floor(ax, ox, oy, fw, fh):
    # fw = EXT_L (116 mm), fh = EXT_W (86 mm)

    # Outer shell
    _r(ax, ox, oy, fw, fh, fc=WALL_FC, ec=WALL_EC, lw=1.2)
    # Interior cavity
    _r(ax, ox + P.WALL, oy + P.WALL, P.INT_L, P.INT_W,
       fc=CAVITY_FC, ec='#888', lw=0.6)

    # Pi PCB footprint (dashed blue)
    px = ox + P.WALL + P.PI_X0_INT
    py = oy + P.WALL + P.PI_Y0_INT
    _r(ax, px, py, P.PI_L, P.PI_W,
       fc='#E3F2FD', ec=COMP_EC, lw=0.8, ls='--', alpha=0.5, zorder=3)
    _txt(ax, px + P.PI_L / 2, py + P.PI_W / 2,
         f"Raspberry Pi 4B\n{P.PI_L}×{P.PI_W} mm", size=4.5, color=COMP_EC)

    # Pi standoffs (outer OD ring + pilot hole)
    for ix, iy in P.pi_hole_positions_interior():
        ex = ox + P.WALL + ix
        ey = oy + P.WALL + iy
        _c(ax, ex, ey, P.STANDOFF_OD, fc=BOSS_FC, ec=BOSS_EC, lw=0.7)
        _c(ax, ex, ey, P.STANDOFF_HOLE_D, fc=PILOT_FC, ec=PILOT_EC, lw=0.8)

    # Quectel adapter top-down shadow (mounted on back wall)
    qu_x  = ox + P.WALL + P.QU_WALL_X0_INT
    # Back wall interior face (Y exterior) = EXT_W - WALL
    back_y_page = oy + P.EXT_W - P.WALL
    qu_depth = P.QU_MOUNT_POST_H + P.QU_H          # total depth from wall into interior
    _r(ax, qu_x, back_y_page - qu_depth, P.QU_L, qu_depth,
       fc='#FFF9C4', ec=COMP_EC, lw=0.7, ls='--', alpha=0.6, zorder=3)
    _txt(ax, qu_x + P.QU_L / 2, back_y_page - qu_depth / 2,
         f"Quectel adapter\n{P.QU_L}×{P.QU_H} mm (wall-mounted)", size=3.8, color=COMP_EC)

    # Face outline (redraw on top)
    _r(ax, ox, oy, fw, fh, fc='none', ec=WALL_EC, lw=1.2)

    # Key dimensions
    _dim_h(ax, ox, ox + fw, oy - 7, f"{fw:.0f}")
    _dim_v(ax, ox + fw + 7, oy, oy + fh, f"{fh:.0f}")
    _dim_h(ax, ox + P.WALL, ox + P.WALL + P.INT_L, oy + P.WALL - 7,
           f"INT={P.INT_L:.0f}", size=3.5)

    # Edge labels
    _txt(ax, ox + fw / 2, oy - 12, "↑  FRONT WALL (Y = 0)", size=4.5, color='#777')
    _txt(ax, ox + fw / 2, oy + fh + 3, "BACK WALL (Y = EXT_W = 86)  ↓", size=4.5, color='#777')
    _txt(ax, ox - 4, oy + fh / 2, "LEFT\n(X=0)", size=4, color='#777', ha='right')
    _txt(ax, ox + fw + 4, oy + fh / 2, "RIGHT\n(X=EXT_L)", size=4, color='#777', ha='left')

    # Standoff legend
    _c(ax, ox + 8, oy + fh - 7, P.STANDOFF_OD, fc=BOSS_FC, ec=BOSS_EC, lw=0.7)
    _c(ax, ox + 8, oy + fh - 7, P.STANDOFF_HOLE_D, fc=PILOT_FC, ec=PILOT_EC, lw=0.8)
    _txt(ax, ox + 18, oy + fh - 7,
         f"Pi standoff  OD={P.STANDOFF_OD} / pilot={P.STANDOFF_HOLE_D} mm",
         size=4, color='#555', ha='left')


# ── PAGE 2: Right short wall ──────────────────────────────────────────────────
# h = Y_ext (front=0 on left → back=86 on right), v = Z_ext (0=bottom)

def draw_right_wall(ax, ox, oy, fw, fh):
    # fw = EXT_W (86 mm), fh = BODY_H (57.5 mm)

    _r(ax, ox, oy, fw, fh, fc=WALL_FC, ec=WALL_EC, lw=1.2)

    # Pi ETH/USB network cutout
    net_y_min = (P.WALL + P.PI_Y0_INT + P.PI_NETPORT_Y[0] - P.NET_CUTOUT_Y_PAD)
    net_y_max = (P.WALL + P.PI_Y0_INT + P.PI_NETPORT_Y[1] + P.NET_CUTOUT_Y_PAD)
    net_z_min = P.FLOOR + P.NET_CUTOUT_Z_MIN
    net_z_max = P.FLOOR + P.NET_CUTOUT_Z_MAX
    nw = net_y_max - net_y_min
    nh = net_z_max - net_z_min
    _r(ax, ox + net_y_min, oy + net_z_min, nw, nh,
       fc=CUT_FC, ec=CUT_EC, lw=0.9, hatch='///', zorder=5)
    _txt(ax, ox + (net_y_min + net_y_max) / 2, oy + (net_z_min + net_z_max) / 2,
         f"Pi ETH + USB-A × 2\n{nw:.1f} × {nh:.1f} mm", size=4, color=CUT_EC)
    _dim_h(ax, ox + net_y_min, ox + net_y_max, oy + net_z_min - 5, f"{nw:.1f}", size=3.5)
    _dim_v(ax, ox + net_y_max + 5, oy + net_z_min, oy + net_z_max, f"{nh:.1f}", size=3.5)

    # GPIO wire pass-through slot
    g_yc = P.WALL + P.GPIO_PASS_Y_CENTER_INT
    g_zc = P.FLOOR + P.GPIO_PASS_Z
    _r(ax, ox + g_yc - P.GPIO_PASS_W / 2, oy + g_zc - P.GPIO_PASS_H / 2,
       P.GPIO_PASS_W, P.GPIO_PASS_H,
       fc=CUT_FC, ec=CUT_EC, lw=0.9, hatch='///', zorder=5)
    _txt(ax, ox + g_yc, oy + g_zc,
         f"GPIO slot\n{P.GPIO_PASS_W}×{P.GPIO_PASS_H}", size=3.8, color=CUT_EC)

    # Face outline
    _r(ax, ox, oy, fw, fh, fc='none', ec=WALL_EC, lw=1.2)

    # Overall dims
    _dim_h(ax, ox, ox + fw, oy - 6, f"{fw:.0f}")
    _dim_v(ax, ox + fw + 6, oy, oy + fh, f"{fh:.0f}")

    # Z ref lines (PCB top, standoff top)
    for z_int, lbl, clr in [
        (P.STANDOFF_H, f"Pi PCB bottom  Z={P.FLOOR+P.STANDOFF_H:.1f}", '#42A5F5'),
        (P.NET_CUTOUT_Z_MIN, None, 'none'),
    ]:
        z_page = oy + P.FLOOR + z_int
        ax.plot([ox, ox + fw], [z_page, z_page],
                color='#BDBDBD', lw=0.4, ls=':', zorder=1)

    # Edge labels
    _txt(ax, ox + fw / 2, oy - 11,
         "FRONT (Y=0) ←──────────────────→ BACK (Y=86)", size=4.5, color='#777')
    _txt(ax, ox - 4, oy + fh / 2, "Z\n▲", size=4.5, color='#777', ha='right')


# ── PAGE 3: Left short wall ───────────────────────────────────────────────────
# h = Y_ext (front=0 on left → back=86 on right), v = Z_ext

def draw_left_wall(ax, ox, oy, fw, fh):
    # fw = EXT_W (86 mm), fh = BODY_H (57.5 mm)

    _r(ax, ox, oy, fw, fh, fc=WALL_FC, ec=WALL_EC, lw=1.2)

    # ── LTE holes (back corner, vertical stack) ──
    lte = P.lte_left_wall_positions()
    for ay, az in lte:
        _c(ax, ox + ay, oy + az, P.ANT_HOLE_D, fc=CUT_FC, ec=CUT_EC, lw=0.9)
    # Vertical spacing dimension
    for i in range(len(lte) - 1):
        _dim_v(ax, ox + lte[0][0] + 8, oy + lte[i][1], oy + lte[i+1][1],
               f"{lte[i+1][1]-lte[i][1]:.0f}", size=3.5)
    # Label first hole
    _txt(ax, ox + lte[0][0] + 7, oy + lte[0][1],
         f"LTE × 3\nD={P.ANT_HOLE_D}", size=4, color=CUT_EC, ha='left')

    # ── RFD holes (front corner, vertical stack) ──
    rfd = P.rfd_left_wall_positions()
    for ay, az in rfd:
        _c(ax, ox + ay, oy + az, P.ANT_HOLE_D, fc=CUT_FC, ec=CUT_EC, lw=0.9)
    # Spacing dimension
    _dim_v(ax, ox + rfd[0][0] - 8, oy + rfd[0][1], oy + rfd[1][1],
           f"{rfd[1][1]-rfd[0][1]:.0f}", size=3.5)
    _txt(ax, ox + rfd[0][0] - 7, oy + (rfd[0][1]+rfd[1][1]) / 2,
         f"RFD × 2\nD={P.ANT_HOLE_D}", size=4, color=CUT_EC, ha='right')

    # ── CAN port (centre of wall) ──
    _c(ax, ox + P.CAN_HOLE_Y_WORLD, oy + P.CAN_HOLE_Z_WORLD, P.CAN_HOLE_D,
       fc=CUT_FC, ec=CUT_EC, lw=0.9)
    _txt(ax, ox + P.CAN_HOLE_Y_WORLD, oy + P.CAN_HOLE_Z_WORLD,
         f"CAN\nD={P.CAN_HOLE_D:.0f}", size=4, color=CUT_EC)

    # Y positions of hole groups from front edge
    _dim_h(ax, ox, ox + rfd[0][0], oy + fh + 5,
           f"{rfd[0][0]:.0f}", size=3.5)
    _dim_h(ax, ox, ox + P.CAN_HOLE_Y_WORLD, oy + fh + 10,
           f"{P.CAN_HOLE_Y_WORLD:.0f}", size=3.5)
    _dim_h(ax, ox, ox + lte[0][0], oy + fh + 15,
           f"{lte[0][0]:.0f}", size=3.5)

    _r(ax, ox, oy, fw, fh, fc='none', ec=WALL_EC, lw=1.2)

    _dim_h(ax, ox, ox + fw, oy - 6, f"{fw:.0f}")
    _dim_v(ax, ox + fw + 6, oy, oy + fh, f"{fh:.0f}")

    _txt(ax, ox + fw / 2, oy - 11,
         "FRONT (Y=0) ←──────────────────→ BACK (Y=86)", size=4.5, color='#777')


# ── PAGE 4: Front long wall ───────────────────────────────────────────────────
# h = X_ext (left wall X=0 → right wall X=116), v = Z_ext

def draw_front_wall(ax, ox, oy, fw, fh):
    # fw = EXT_L (116 mm), fh = BODY_H (57.5 mm)

    _r(ax, ox, oy, fw, fh, fc=WALL_FC, ec=WALL_EC, lw=1.2)

    # Pi media cutout (USB-C / HDMI × 2 / Audio)
    pi_x_w = P.WALL + P.PI_X0_INT
    mx1 = pi_x_w + P.PI_USBC_X[0]  - P.MEDIA_CUTOUT_PAD_X
    mx2 = pi_x_w + P.PI_AUDIO_X[1] + P.MEDIA_CUTOUT_PAD_X
    mz1 = P.FLOOR + P.MEDIA_CUTOUT_Z_MIN
    mz2 = P.FLOOR + P.MEDIA_CUTOUT_Z_MAX
    mw = mx2 - mx1
    mh = mz2 - mz1
    _r(ax, ox + mx1, oy + mz1, mw, mh,
       fc=CUT_FC, ec=CUT_EC, lw=0.9, hatch='///', zorder=5)
    _txt(ax, ox + (mx1 + mx2) / 2, oy + (mz1 + mz2) / 2,
         f"Pi media ports\n(USB-C / HDMI×2 / Audio)\n{mw:.1f}×{mh:.1f} mm",
         size=4, color=CUT_EC)
    _dim_h(ax, ox + mx1, ox + mx2, oy + mz1 - 5, f"{mw:.1f}", size=3.5)
    _dim_v(ax, ox + mx2 + 5, oy + mz1, oy + mz2, f"{mh:.1f}", size=3.5)

    # Vent slots
    sp = P.EXT_L / (P.SIDE_VENT_COUNT_PER_LONG_WALL + 1)
    cz = P.FLOOR + P.SIDE_VENT_Z_CENTER
    for i in range(1, P.SIDE_VENT_COUNT_PER_LONG_WALL + 1):
        cx = i * sp
        _r(ax, ox + cx - P.SIDE_VENT_L / 2, oy + cz - P.SIDE_VENT_W / 2,
           P.SIDE_VENT_L, P.SIDE_VENT_W,
           fc=CUT_FC, ec=CUT_EC, lw=0.7, hatch='///', zorder=5)
    _txt(ax, ox + (2 * sp), oy + cz + 4,
         f"Vent slots ({P.SIDE_VENT_COUNT_PER_LONG_WALL}× each long wall)\n"
         f"{P.SIDE_VENT_L}×{P.SIDE_VENT_W} mm  Z={cz:.1f}",
         size=3.5, color=CUT_EC)

    _r(ax, ox, oy, fw, fh, fc='none', ec=WALL_EC, lw=1.2)
    _dim_h(ax, ox, ox + fw, oy - 6, f"{fw:.0f}")
    _dim_v(ax, ox + fw + 6, oy, oy + fh, f"{fh:.0f}")

    # Pi PCB left edge reference line
    ax.plot([ox + pi_x_w, ox + pi_x_w], [oy, oy + fh],
            color='#90CAF9', lw=0.5, ls=':', zorder=1)
    _txt(ax, ox + pi_x_w + 1, oy + 3, f"Pi X={pi_x_w:.0f}", size=3.5, color='#90CAF9', ha='left')

    _txt(ax, ox + fw / 2, oy - 11,
         "LEFT (X=0) ←──────────────────────→ RIGHT (X=116)", size=4.5, color='#777')


# ── PAGE 5: Back long wall (interior face) ────────────────────────────────────
# h = X_ext (left wall X=0 → right wall X=116), v = Z_ext

def draw_back_wall(ax, ox, oy, fw, fh):
    # fw = EXT_L (116 mm), fh = BODY_H (57.5 mm)

    _r(ax, ox, oy, fw, fh, fc=WALL_FC, ec=WALL_EC, lw=1.2)

    # Quectel adapter PCB footprint (dashed yellow)
    qu_x = P.WALL + P.QU_WALL_X0_INT
    qu_z = P.FLOOR + P.QU_WALL_Z0_INT
    _r(ax, ox + qu_x, oy + qu_z, P.QU_L, P.QU_W,
       fc='#FFF9C4', ec=COMP_EC, lw=0.8, ls='--', alpha=0.6, zorder=3)
    _txt(ax, ox + qu_x + P.QU_L / 2, oy + qu_z + P.QU_W / 2,
         f"Quectel adapter footprint\n{P.QU_L} × {P.QU_W} mm", size=4.5, color=COMP_EC)

    # Mounting boss + pilot holes (4 corners of adapter PCB)
    holes = P.quectel_wall_hole_positions()
    for ix, iz in holes:
        ex = ox + P.WALL + ix
        ez = oy + P.FLOOR + iz
        _c(ax, ex, ez, P.QU_MOUNT_POST_OD, fc=BOSS_FC, ec=BOSS_EC, lw=0.7)
        _c(ax, ex, ez, P.QU_MOUNT_PILOT_D, fc=PILOT_FC, ec=PILOT_EC, lw=0.9)

    # Dimension: hole-to-hole X span
    hx0 = ox + P.WALL + holes[0][0]
    hx1 = ox + P.WALL + holes[1][0]
    hz0 = oy + P.FLOOR + holes[0][1]
    hz1 = oy + P.FLOOR + holes[2][1]
    _dim_h(ax, hx0, hx1, oy + qu_z - 6, f"{holes[1][0]-holes[0][0]:.2f}", size=3.5)
    _dim_v(ax, ox + P.WALL + holes[1][0] + 7, hz0, hz1,
           f"{holes[2][1]-holes[0][1]:.2f}", size=3.5)

    # X offset of adapter left edge from left interior wall
    _dim_h(ax, ox + P.WALL, ox + qu_x, oy + fh + 5, f"{P.QU_WALL_X0_INT:.0f}", size=3.5)

    # Vent slots
    sp = P.EXT_L / (P.SIDE_VENT_COUNT_PER_LONG_WALL + 1)
    cz = P.FLOOR + P.SIDE_VENT_Z_CENTER
    for i in range(1, P.SIDE_VENT_COUNT_PER_LONG_WALL + 1):
        cx = i * sp
        _r(ax, ox + cx - P.SIDE_VENT_L / 2, oy + cz - P.SIDE_VENT_W / 2,
           P.SIDE_VENT_L, P.SIDE_VENT_W,
           fc=CUT_FC, ec=CUT_EC, lw=0.7, hatch='///', zorder=5)

    _r(ax, ox, oy, fw, fh, fc='none', ec=WALL_EC, lw=1.2)
    _dim_h(ax, ox, ox + fw, oy - 6, f"{fw:.0f}")
    _dim_v(ax, ox + fw + 6, oy, oy + fh, f"{fh:.0f}")

    _txt(ax, ox + fw / 2, oy - 11,
         "LEFT (X=0) ←──────────────────────→ RIGHT (X=116)", size=4.5, color='#777')
    _txt(ax, ox + fw / 2, oy + fh + 4,
         "(INTERIOR face — Quectel bosses project inward toward you)", size=4.5, color='#777')


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    EXPORTS.mkdir(parents=True, exist_ok=True)
    out = EXPORTS / "face_templates.pdf"

    pages = [
        ("FLOOR PLAN  ·  top view (look from above into open enclosure)",
         f"Interior {P.INT_L:.0f}×{P.INT_W:.0f} mm  |  Exterior {P.EXT_L:.0f}×{P.EXT_W:.0f} mm"
         "  |  ⬤ Pi standoffs  ⬤ Quectel shadow",
         P.EXT_L, P.EXT_W, draw_floor),

        ("RIGHT SHORT WALL  ·  Pi ETH + USB + GPIO pass-through",
         "Look from outside (+X direction)  |  h = Y (front→back)  |  v = Z (bottom→top)",
         P.EXT_W, P.BODY_H, draw_right_wall),

        ("LEFT SHORT WALL  ·  Antenna holes + CAN port",
         f"Look from outside (−X direction)  |  3× LTE  +  2× RFD  +  1× CAN  |  D={P.ANT_HOLE_D} mm SMA",
         P.EXT_W, P.BODY_H, draw_left_wall),

        ("FRONT LONG WALL  ·  Pi media ports + vent slots",
         "Look from outside (−Y direction)  |  h = X (left wall → right wall)  |  v = Z",
         P.EXT_L, P.BODY_H, draw_front_wall),

        ("BACK LONG WALL — INTERIOR FACE  ·  Quectel adapter mount + vent slots",
         "Look from inside the enclosure toward the back wall  |  h = X (left→right)  |  v = Z",
         P.EXT_L, P.BODY_H, draw_back_wall),
    ]

    with PdfPages(out) as pdf:
        for title, subtitle, fw, fh, fn in pages:
            make_page(pdf, title, subtitle, fw, fh, fn)

    sz = out.stat().st_size // 1024
    print(f"Saved {out}  ({sz} KB, {len(pages)} pages)")
    print()
    print("Pages:")
    for i, (t, *_) in enumerate(pages, 1):
        print(f"  {i}. {t}")
    print()
    print("HOW TO USE:")
    print("  1. Open face_templates.pdf in any PDF viewer")
    print("  2. Print at EXACTLY 100% scale (no fit-to-page, no scaling)")
    print("  3. Verify the 30 mm scale bar measures 30 mm with a ruler")
    print("  4. Cut around the grey face rectangle; lay components on top to check fit")
    print("     - Page 1: place Pi PCB, check standoff holes align")
    print("     - Page 2: hold Pi against right wall cutout")
    print("     - Page 3: check SMA connectors fit the antenna holes")
    print("     - Page 5: hold Quectel adapter against back wall, check mounting holes")


if __name__ == "__main__":
    main()
