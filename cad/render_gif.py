#!/usr/bin/env python3
"""
Render a turntable animated GIF of the enclosure body + lid STL.
Usage:  tools/render-venv/bin/python cad/render_gif.py [car-1.5|car-2]
Output: exports/<version>/enclosure_preview.gif
"""
import argparse
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from stl import mesh
from PIL import Image
import io

HERE = Path(__file__).resolve().parent

parser = argparse.ArgumentParser(description="Render enclosure turntable GIF")
parser.add_argument("version", nargs="?", default="car-1.5",
                    choices=["car-1.5", "car-2"],
                    help="which export folder to render (default: car-1.5)")
args = parser.parse_args()
EXPORTS = HERE.parent / "exports" / args.version

# ── Load STL files ──────────────────────────────────────────────────────────

def load_stl(path: Path):
    m = mesh.Mesh.from_file(str(path))
    # vectors shape: (n_faces, 3 verts, 3 xyz)
    return m.vectors, m.normals

body_verts, body_norms = load_stl(EXPORTS / "enclosure_body.stl")
lid_verts,  lid_norms  = load_stl(EXPORTS / "enclosure_lid.stl")

if args.version == "car-2":
    # car-2 files are Y-up. Revert to Z-up (+90 deg X rot) for matplotlib
    for verts in [body_verts, lid_verts]:
        y_tmp = verts[:, :, 1].copy()
        z_tmp = verts[:, :, 2].copy()
        verts[:, :, 1] = -z_tmp
        verts[:, :, 2] = y_tmp

# Centre both meshes on their combined bounding box
all_pts = np.vstack([body_verts.reshape(-1, 3), lid_verts.reshape(-1, 3)])
centre  = (all_pts.max(axis=0) + all_pts.min(axis=0)) / 2
span    = (all_pts.max(axis=0) - all_pts.min(axis=0)).max()

body_verts = body_verts - centre
lid_verts  = lid_verts  - centre

# Offset lid upward by a tiny gap so the two meshes don't z-fight
lid_verts = lid_verts + np.array([0, 0, 0.4])

# ── Render settings ─────────────────────────────────────────────────────────

N_FRAMES  = 40          # frames in the loop
ELEV      = 28          # camera elevation (degrees)
DPI       = 110
FIG_SIZE  = (5.5, 4.5)
LIM       = span * 0.58  # axis half-range

BODY_COLOR = "#4A90D9"   # steel blue
LID_COLOR  = "#6FBDE8"   # lighter blue
BODY_ALPHA = 0.92
LID_ALPHA  = 0.78        # slightly transparent so interior bosses hint through

# ── Per-frame lighting: shade faces by their normal vs view direction ────────

def shade_alpha(normals, azimuth_deg, elev_deg, base_alpha, lo=0.3, hi=1.0):
    az  = np.radians(azimuth_deg)
    el  = np.radians(elev_deg)
    light = np.array([np.cos(el) * np.cos(az),
                      np.cos(el) * np.sin(az),
                      np.sin(el)])
    # unit normals
    mag = np.linalg.norm(normals, axis=1, keepdims=True)
    mag = np.where(mag == 0, 1, mag)
    n   = normals / mag
    dot = np.clip(n @ light, 0, 1)
    return base_alpha * np.clip(lo + (hi - lo) * dot, lo, hi)


# ── Build frames ─────────────────────────────────────────────────────────────

frames: list[Image.Image] = []
azimuths = np.linspace(0, 360, N_FRAMES, endpoint=False)

for az in azimuths:
    fig = plt.figure(figsize=FIG_SIZE, dpi=DPI)
    ax  = fig.add_subplot(111, projection="3d")
    fig.patch.set_facecolor("#1A1A2E")
    ax.set_facecolor("#1A1A2E")

    # Remove axis decorations for a clean look
    ax.set_axis_off()
    ax.set_xlim(-LIM, LIM)
    ax.set_ylim(-LIM, LIM)
    ax.set_zlim(-LIM, LIM)

    # Body
    b_alpha = shade_alpha(body_norms.reshape(-1, 3), az, ELEV, BODY_ALPHA)
    b_coll  = Poly3DCollection(body_verts, zsort="average", edgecolor="none")
    b_coll.set_facecolor(
        np.column_stack([
            np.tile(matplotlib.colors.to_rgb(BODY_COLOR), (len(body_verts), 1)),
            b_alpha,
        ])
    )
    ax.add_collection3d(b_coll)

    # Lid
    l_alpha = shade_alpha(lid_norms.reshape(-1, 3), az, ELEV, LID_ALPHA)
    l_coll  = Poly3DCollection(lid_verts, zsort="average", edgecolor="none")
    l_coll.set_facecolor(
        np.column_stack([
            np.tile(matplotlib.colors.to_rgb(LID_COLOR), (len(lid_verts), 1)),
            l_alpha,
        ])
    )
    ax.add_collection3d(l_coll)

    ax.view_init(elev=ELEV, azim=az)
    plt.tight_layout(pad=0)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=DPI,
                facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.05)
    buf.seek(0)
    frames.append(Image.open(buf).copy())
    plt.close(fig)

# ── Save GIF ─────────────────────────────────────────────────────────────────

out = EXPORTS / "enclosure_preview.gif"
frames[0].save(
    out,
    save_all=True,
    append_images=frames[1:],
    loop=0,
    duration=70,       # ms per frame
    optimize=True,
)

print(f"Saved {out}  ({out.stat().st_size // 1024} KB, {N_FRAMES} frames)")
