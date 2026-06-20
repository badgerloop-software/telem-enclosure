#!/usr/bin/env python3
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch
from matplotlib.backends.backend_pdf import PdfPages

EXPORTS = Path(__file__).resolve().parent.parent / "exports" / "car-2"

# Page layout
MARGIN_X, MARGIN_Y, HDR, FTR = 22, 18, 14, 16
WALL_FC, WALL_EC = "#DEDEDE", "#333333"
CAVITY_FC = "#FFFFFF"
CUT_FC, CUT_EC = "#FFCDD2", "#C62828"
DIM_C, WARN_C = "#5D4037", "#B71C1C"

def _r(ax, x, y, w, h, fc=CAVITY_FC, ec=WALL_EC, lw=0.8, ls='-', hatch=None):
    kw = dict(facecolor=fc, edgecolor=ec, linewidth=lw, linestyle=ls)
    if hatch: kw['hatch'] = hatch
    ax.add_patch(Rectangle((x, y), w, h, **kw))

def _c(ax, cx, cy, d, fc=CUT_FC, ec=CUT_EC, lw=0.8):
    ax.add_patch(Circle((cx, cy), d / 2, facecolor=fc, edgecolor=ec, linewidth=lw))

def _txt(ax, x, y, text, size=4.5, color='#333', ha='center', va='center', **kw):
    ax.text(x, y, text, fontsize=size, color=color, ha=ha, va=va, **kw)

def _dim_h(ax, x1, x2, y, label):
    ax.annotate('', xy=(x2, y), xytext=(x1, y), arrowprops=dict(arrowstyle='<->', color=DIM_C, lw=0.55))
    for xp in (x1, x2): ax.plot([xp, xp], [y-1, y+1], color=DIM_C, lw=0.55)
    _txt(ax, (x1+x2)/2, y+1.8, label, size=4, color=DIM_C)

def _dim_v(ax, x, y1, y2, label):
    ax.annotate('', xy=(x, y2), xytext=(x, y1), arrowprops=dict(arrowstyle='<->', color=DIM_C, lw=0.55))
    for yp in (y1, y2): ax.plot([x-1, x+1], [yp, yp], color=DIM_C, lw=0.55)
    _txt(ax, x+2.5, (y1+y2)/2, label, size=4, color=DIM_C, rotation=90, rotation_mode='anchor', ha='left')

def _scale_bar(ax, x, y, length=30):
    ax.plot([x, x+length], [y, y], 'k-', lw=1.3)
    for xp in (x, x+length): ax.plot([xp, xp], [y-2, y+2], 'k-', lw=1.0)
    _txt(ax, x+length/2, y+3, f'{length} mm', size=5.5)

def make_page(pdf, title, subtitle, face_w, face_h, draw_fn):
    total_w = face_w + 2*MARGIN_X
    total_h = face_h + HDR + FTR + MARGIN_Y
    fig, ax = plt.subplots(figsize=(total_w/25.4, total_h/25.4))
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_xlim(0, total_w)
    ax.set_ylim(0, total_h)
    fig.patch.set_facecolor('#FAFAFA')
    ax.add_patch(FancyBboxPatch((0.5, 0.5), total_w-1, total_h-1, boxstyle="square,pad=0", edgecolor='#BBB', facecolor='none', lw=0.4))
    ox = MARGIN_X
    oy = FTR + MARGIN_Y/2
    draw_fn(ax, ox, oy, face_w, face_h)
    _txt(ax, total_w/2, oy+face_h+HDR*0.75, title, size=8.5, color='#111', fontweight='bold')
    _txt(ax, total_w/2, oy+face_h+HDR*0.2, subtitle, size=5, color='#555')
    _scale_bar(ax, MARGIN_X, FTR*0.4, 30)
    _txt(ax, total_w*0.62, FTR*0.4, "⚠ PRINT AT 100% · DISABLE FIT TO PAGE", size=5, color=WARN_C, ha='center')
    pdf.savefig(fig)
    plt.close(fig)

# DIMS
EXT_L = 228.6
EXT_W = 101.6
BODY_H = 57.15
WALL = 7.62

def draw_floor(ax, ox, oy, fw, fh):
    _r(ax, ox, oy, fw, fh, fc=WALL_FC)
    _r(ax, ox+WALL, oy+WALL, EXT_L-2*WALL, EXT_W-2*WALL, fc=CAVITY_FC)
    # Pi holes
    PI = [(110.0, 18.0), (110.0, 67.0), (158.5, 18.0), (158.5, 67.0)]
    for px, py in PI:
        _c(ax, ox+px, oy+py, 2.1)
        _c(ax, ox+px, oy+py, 6.0, fc='none', ec="#555")
    _dim_h(ax, ox, ox+fw, oy-7, f"{fw}")
    _dim_v(ax, ox+fw+7, oy, oy+fh, f"{fh}")

def draw_right_wall(ax, ox, oy, fw, fh):
    _r(ax, ox, oy, fw, fh, fc=WALL_FC)
    _r(ax, ox, oy, fw, fh, fc='none', ec=WALL_EC, lw=1.2)
    # Cutout
    _r(ax, ox+93.98, oy+12.7, 152.4-93.98, 22.86-12.7, fc=CUT_FC, ec=CUT_EC, hatch='///')
    # LTE bosses
    for iz in [10, 20, 30, 40]:
        _c(ax, ox+95.0, oy+iz, 2.54)
    _dim_h(ax, ox, ox+fw, oy-6, f"{fw}")
    _dim_v(ax, ox+fw+6, oy, oy+fh, f"{fh}")

def draw_left_wall(ax, ox, oy, fw, fh):
    _r(ax, ox, oy, fw, fh, fc=WALL_FC)
    _r(ax, ox, oy, fw, fh, fc='none', ec=WALL_EC, lw=1.2)
    # Camera hole
    _c(ax, ox+50.8, oy+29.21, 11.5)
    _dim_h(ax, ox, ox+fw, oy-6, f"{fw}")
    _dim_v(ax, ox+fw+6, oy, oy+fh, f"{fh}")

def main():
    EXPORTS.mkdir(parents=True, exist_ok=True)
    out = EXPORTS / "face_templates.pdf"
    with PdfPages(out) as pdf:
        make_page(pdf, "FLOOR PLAN", "Top view", EXT_L, EXT_W, draw_floor)
        make_page(pdf, "RIGHT SHORT WALL", "Cutout + LTE holes", EXT_W, BODY_H, draw_right_wall)
        make_page(pdf, "LEFT SHORT WALL", "Camera hole", EXT_W, BODY_H, draw_left_wall)
    print(f"Saved {out}")

if __name__ == "__main__":
    main()
