"""Build the compact telemetry enclosure (body + lid) in FreeCAD.

Run headless from the project root:

    freecadcmd cad/enclosure.py

Or open FreeCAD GUI -> Macro -> open this file and run.

Outputs into ../exports/car-2 relative to this file:
    enclosure_body.FCStd, enclosure_body.step, enclosure_body.stl
    enclosure_lid.FCStd,  enclosure_lid.step,  enclosure_lid.stl
    telem_enclosure_assembly.FCStd  (body + lid + reference component bricks)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import FreeCAD as App
import Part
import Mesh

# Make `params` importable when run via freecadcmd or exec()
try:
    HERE = Path(__file__).resolve().parent
except NameError:
    cwd = Path.cwd().resolve()
    HERE = cwd / "cad" if (cwd / "cad" / "params.py").exists() else cwd
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import params as P  # noqa: E402


EXPORT_DIR = HERE.parent / "exports" / "car-2"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

def _box(x, y, z, dx, dy, dz):
    """Axis-aligned box positioned at (x,y,z) with size (dx,dy,dz)."""
    b = Part.makeBox(dx, dy, dz)
    b.translate(App.Vector(x, y, z))
    return b


def _cyl(x, y, z, d, h, dir_=(0, 0, 1)):
    c = Part.makeCylinder(d / 2.0, h, App.Vector(x, y, z), App.Vector(*dir_))
    return c


def _interior_to_exterior(x, y, z):
    """Convert an interior-frame point (X in 0..INT_L, Y in 0..INT_W, Z above
    interior floor) into the body's exterior frame used by Part shapes."""
    return (x + P.WALL, y + P.WALL, z + P.FLOOR)


def _slot(x_center, y_center, z_center, length_x, length_y, length_z):
    """Centered axis-aligned box for cutouts."""
    return _box(
        x_center - length_x / 2.0,
        y_center - length_y / 2.0,
        z_center - length_z / 2.0,
        length_x,
        length_y,
        length_z,
    )


# ----------------------------------------------------------------------------
# Body
# ----------------------------------------------------------------------------

def build_body() -> Part.Shape:
    """Construct the enclosure body shell with standoffs, shelves and cutouts."""

    # Outer block, then carve cavity from the top to leave the floor.
    outer = _box(0, 0, 0, P.EXT_L, P.EXT_W, P.BODY_H)
    cavity = _box(P.WALL, P.WALL, P.FLOOR,
                  P.INT_L, P.INT_W, P.INT_H + P.LID + 1.0)
    body = outer.cut(cavity)

    # ---- Pi standoffs ----
    standoff_solids = []
    standoff_holes = []
    for ix, iy in P.pi_hole_positions_interior():
        ex, ey, _ = _interior_to_exterior(ix, iy, 0)
        standoff_solids.append(
            _cyl(ex, ey, P.FLOOR, P.STANDOFF_OD, P.STANDOFF_H)
        )
        standoff_holes.append(
            _cyl(ex, ey,
                 P.FLOOR + P.STANDOFF_H - P.STANDOFF_HOLE_DEPTH,
                 P.STANDOFF_HOLE_D,
                 P.STANDOFF_HOLE_DEPTH + P.EPS)
        )
    for s in standoff_solids:
        body = body.fuse(s)
    for h in standoff_holes:
        body = body.cut(h)

    # ---- Lid screw bosses (hang from top of body walls so they don't
    # collide with the Pi PCB sitting in the +X/-Y corner) ----
    boss_h = 10.0           # how far the boss hangs down from the wall top
    cavity_vol = _box(P.WALL, P.WALL, P.FLOOR,
                      P.INT_L, P.INT_W, P.INT_H)
    for sx, sy in P.lid_screw_positions_exterior():
        boss = _cyl(sx, sy, P.BODY_H - boss_h,
                    P.LID_SCREW_BOSS_OD, boss_h)
        boss_in = boss.common(cavity_vol)
        body = body.fuse(boss_in)
        # Self-tap pilot hole, drilled from the top
        hole = _cyl(sx, sy, P.BODY_H - boss_h - P.EPS,
                    P.LID_SCREW_BOSS_HOLE_D, boss_h + 2 * P.EPS)
        body = body.cut(hole)

    # ---- Quectel adapter: wall-mount bosses on back wall interior face ----
    # The adapter PCB sits flat against the back wall, held on 4 standoff
    # bosses (QU_MOUNT_POST_H = 3 mm) with M3 self-tap screws through the PCB.
    # Bosses project in the -Y direction from Y = WALL+INT_W.
    back_wall_y = P.WALL + P.INT_W
    for ix, iz in P.quectel_wall_hole_positions():
        ex = P.WALL + ix
        ez = P.FLOOR + iz
        boss = _cyl(ex, back_wall_y, ez,
                    P.QU_MOUNT_POST_OD, P.QU_MOUNT_POST_H, dir_=(0, -1, 0))
        body = body.fuse(boss)
        # Pilot drilled inward from the interior face (deeper than the boss)
        pilot = _cyl(ex, back_wall_y + P.EPS, ez,
                     P.QU_MOUNT_PILOT_D, P.QU_MOUNT_PILOT_DEPTH, dir_=(0, -1, 0))
        body = body.cut(pilot)

    # RTC mounts directly on Pi GPIO pins — no enclosure platform.

    # ---- Pi I/O cutout: media long edge on Y=0 wall ----
    media_z_min = P.FLOOR + P.MEDIA_CUTOUT_Z_MIN
    media_z_max = P.FLOOR + P.MEDIA_CUTOUT_Z_MAX
    media_dz = media_z_max - media_z_min
    pi_x_world = P.WALL + P.PI_X0_INT
    # Single combined slot covering USB-C through audio jack (X-range).
    media_x_min = pi_x_world + P.PI_USBC_X[0] - P.MEDIA_CUTOUT_PAD_X
    media_x_max = pi_x_world + P.PI_AUDIO_X[1] + P.MEDIA_CUTOUT_PAD_X
    media_cutout = _box(
        media_x_min, -P.EPS, media_z_min,
        media_x_max - media_x_min,
        P.WALL + 2 * P.EPS,
        media_dz,
    )
    body = body.cut(media_cutout)

    # ---- Pi I/O cutout: network short edge on X=INT_L wall (right) ----
    net_z_min = P.FLOOR + P.NET_CUTOUT_Z_MIN
    net_z_max = P.FLOOR + P.NET_CUTOUT_Z_MAX
    pi_y_world = P.WALL + P.PI_Y0_INT
    net_y_min = pi_y_world + P.PI_NETPORT_Y[0] - P.NET_CUTOUT_Y_PAD
    net_y_max = pi_y_world + P.PI_NETPORT_Y[1] + P.NET_CUTOUT_Y_PAD
    net_cutout = _box(
        P.WALL + P.INT_L - P.EPS,
        net_y_min,
        net_z_min,
        P.WALL + 2 * P.EPS,
        net_y_max - net_y_min,
        net_z_max - net_z_min,
    )
    body = body.cut(net_cutout)

    # ---- GPIO wire pass-through on X=INT_L wall (right short wall) ----
    # Sits below the Pi network/USB cutout, centered on the same Y span.
    gpio_y_world = P.WALL + P.GPIO_PASS_Y_CENTER_INT
    gpio_z_world = P.FLOOR + P.GPIO_PASS_Z
    gpio_cutout = _slot(
        P.WALL + P.INT_L + P.WALL / 2.0,  # centered through the right wall
        gpio_y_world,
        gpio_z_world,
        P.WALL + 2 * P.EPS,
        P.GPIO_PASS_W,
        P.GPIO_PASS_H,
    )
    body = body.cut(gpio_cutout)

    # ---- Side vent slots on long walls ----
    for wall_y, dir_y in [(0.0, -1.0), (P.EXT_W, 1.0)]:
        spacing = P.EXT_L / (P.SIDE_VENT_COUNT_PER_LONG_WALL + 1)
        for i in range(1, P.SIDE_VENT_COUNT_PER_LONG_WALL + 1):
            cx = i * spacing
            cz = P.FLOOR + P.SIDE_VENT_Z_CENTER
            slot = _slot(
                cx,
                wall_y + dir_y * P.WALL / 2.0,
                cz,
                P.SIDE_VENT_L,
                P.WALL + 2 * P.EPS,
                P.SIDE_VENT_W,
            )
            body = body.cut(slot)

    # ---- Left short wall (X = 0): 3 LTE + 2 RFD SMA holes + 1 CAN port ----
    # LTE — vertical stack, near back edge
    for ay_w, az_w in P.lte_left_wall_positions():
        body = body.cut(_cyl(-P.EPS, ay_w, az_w,
                             P.ANT_HOLE_D, P.WALL + 2 * P.EPS, dir_=(1, 0, 0)))
    # RFD900A — vertical stack, 20 mm apart, near front edge
    for ay_w, az_w in P.rfd_left_wall_positions():
        body = body.cut(_cyl(-P.EPS, ay_w, az_w,
                             P.ANT_HOLE_D, P.WALL + 2 * P.EPS, dir_=(1, 0, 0)))
    # CAN port — larger hole in the centre of the wall
    body = body.cut(_cyl(-P.EPS, P.CAN_HOLE_Y_WORLD, P.CAN_HOLE_Z_WORLD,
                         P.CAN_HOLE_D, P.WALL + 2 * P.EPS, dir_=(1, 0, 0)))

    # ---- Chamfer outer bottom edge for printability/feel (1 mm) ----
    try:
        edges = []
        for e in body.Edges:
            verts = e.Vertexes
            if len(verts) < 2:
                continue
            if all(abs(v.Z) < 0.01 for v in verts):
                edges.append(e)
        if edges:
            body = body.makeChamfer(1.0, edges)
    except Exception as exc:  # noqa: BLE001
        App.Console.PrintWarning(f"Skip bottom chamfer: {exc}\n")

    return body


# ----------------------------------------------------------------------------
# Lid
# ----------------------------------------------------------------------------

def build_lid() -> Part.Shape:
    """Construct the lid plate with antenna holes, snap lip and screw holes.

    The lid is built in its own coordinate frame with origin at its outer
    bottom-front-left corner. When mounted, this corner aligns with
    (0, 0, BODY_H) of the body.
    """

    plate = _box(0, 0, 0, P.EXT_L, P.EXT_W, P.LID)

    # Snap lip projecting downward from the underside of the plate.
    lip_inner = _box(
        P.WALL + P.LID_LIP_GAP,
        P.WALL + P.LID_LIP_GAP,
        -P.LID_LIP_DEPTH,
        P.INT_L - 2 * P.LID_LIP_GAP,
        P.INT_W - 2 * P.LID_LIP_GAP,
        P.LID_LIP_DEPTH,
    )
    lip_outer = _box(
        P.WALL + P.LID_LIP_GAP - P.LID_LIP_T,
        P.WALL + P.LID_LIP_GAP - P.LID_LIP_T,
        -P.LID_LIP_DEPTH,
        P.INT_L - 2 * P.LID_LIP_GAP + 2 * P.LID_LIP_T,
        P.INT_W - 2 * P.LID_LIP_GAP + 2 * P.LID_LIP_T,
        P.LID_LIP_DEPTH,
    )
    lip = lip_outer.cut(lip_inner)
    lid = plate.fuse(lip)

    # Antenna holes are on the body walls, not the lid.

    # ---- Lid screw clearance holes at corners ----
    for sx, sy in P.lid_screw_positions_exterior():
        hole = _cyl(sx, sy, -P.EPS, P.LID_SCREW_CLEAR_D, P.LID + 2 * P.EPS)
        lid = lid.cut(hole)

    # ---- Lid vent slots ----
    spacing = P.EXT_L / (P.LID_VENT_COUNT + 1)
    for i in range(1, P.LID_VENT_COUNT + 1):
        cx = i * spacing
        cy = P.EXT_W / 2.0
        slot = _slot(cx, cy, P.LID / 2.0,
                     P.LID_VENT_W, P.LID_VENT_L, P.LID + 2 * P.EPS)
        lid = lid.cut(slot)

    return lid


# ----------------------------------------------------------------------------
# Reference component bricks (for assembly preview / clearance check only)
# ----------------------------------------------------------------------------

def reference_bricks():
    """Yield (label, shape) tuples in the BODY's exterior coordinate frame."""

    # Raspberry Pi 4B (PCB + tallest top-side components, ~20mm)
    pi_x = P.WALL + P.PI_X0_INT
    pi_y = P.WALL + P.PI_Y0_INT
    pi_z = P.FLOOR + P.PI_Z0_INT
    yield (
        "RPi4B",
        _box(pi_x, pi_y, pi_z, P.PI_L, P.PI_W, P.PI_PCB_T + P.PI_USBA_H + 1.0),
    )

    # RFD900A adhered to the left short wall interior face.
    # Show it lying flat against the wall (X=WALL is the inside face).
    rfd_x = P.WALL          # against the left interior wall face
    rfd_y = P.WALL + 5.0    # 5 mm in from front
    rfd_z = P.FLOOR + 10.0  # 10 mm above floor (clear of floor fillet)
    yield ("RFD900A_on_wall", _box(rfd_x, rfd_y, rfd_z, P.RFD_H, P.RFD_W, P.RFD_L))

    # Quectel + Mini PCIe adapter — back wall, PCB face at Y = back_wall - POST_H
    qu_pcb_y = P.WALL + P.INT_W - P.QU_MOUNT_POST_H
    qu_x = P.WALL + P.QU_WALL_X0_INT
    qu_z = P.FLOOR + P.QU_WALL_Z0_INT
    # Adapter: L along X, W along Z, H extends inward (-Y direction)
    yield ("Quectel_EG25-G", _box(qu_x, qu_pcb_y - P.QU_H, qu_z, P.QU_L, P.QU_H, P.QU_W))

    # Adafruit RTC mounts on Pi GPIO pins — no separate reference brick.


# ----------------------------------------------------------------------------
# Clearance reporting
# ----------------------------------------------------------------------------

def clearance_report(body_shape):
    """Print a quick numeric clearance report against the interior cavity."""
    print("\n=== Clearance check ===")
    cavity_top_z = P.FLOOR + P.INT_H
    print(f"Interior height above floor: {P.INT_H:.1f} mm "
          f"(floor Z={P.FLOOR}, lid underside Z={cavity_top_z})")
    pi_top_z = P.FLOOR + P.PI_Z0_INT + P.PI_PCB_T + P.PI_USBA_H
    print(f"Pi USB-A stack top Z: {pi_top_z:.1f} mm "
          f"(headroom to lid: {cavity_top_z - pi_top_z:.1f} mm)")
    # Quectel on back wall: spans Z from QU_WALL_Z0_INT to QU_WALL_Z0_INT+QU_W
    qu_z_top = P.FLOOR + P.QU_WALL_Z0_INT + P.QU_W
    qu_y_front = P.WALL + P.INT_W - P.QU_MOUNT_POST_H - P.QU_H
    pi_y_max_world = P.WALL + P.PI_W
    print(f"Quectel Z span: {P.FLOOR + P.QU_WALL_Z0_INT:.1f}–{qu_z_top:.2f} mm "
          f"(headroom: {cavity_top_z - qu_z_top:.2f} mm)")
    print(f"Quectel front face Y: {qu_y_front:.2f} mm, Pi Y edge: {pi_y_max_world:.1f} mm, "
          f"gap: {qu_y_front - pi_y_max_world:.2f} mm")
    if qu_y_front < pi_y_max_world:
        print("WARNING: Quectel front face overlaps Pi PCB in Y — increase INT_W or reduce QU_H.")
    if qu_z_top > cavity_top_z:
        print("WARNING: Quectel taller than interior. Increase INT_H.")
    rfd_wall_top_z = P.FLOOR + 10.0 + P.RFD_L
    print(f"RFD900A on left wall top Z: {rfd_wall_top_z:.1f} mm (adhesive, no structural feature)")
    print(f"LTE holes (left wall, back corner): {P.lte_left_wall_positions()}")
    print(f"RFD holes (left wall, front corner): {P.rfd_left_wall_positions()}")
    print(f"CAN hole (left wall, centre): Y={P.CAN_HOLE_Y_WORLD} Z={P.CAN_HOLE_Z_WORLD:.2f} D={P.CAN_HOLE_D}mm")
    print("=======================\n")


# ----------------------------------------------------------------------------
# Build and export
# ----------------------------------------------------------------------------

def _save_step(shape, path: Path):
    shape.exportStep(str(path))


def _save_stl(shape, path: Path):
    """Tessellate to mesh and export STL."""
    mesh = Mesh.Mesh()
    mesh.addFacets(shape.tessellate(0.1))
    mesh.write(str(path))


def main():
    body = build_body()
    lid = build_lid()

    clearance_report(body)

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

    # ---- Assembly preview (body + lid translated up + reference bricks) ----
    asm = App.newDocument("telem_enclosure_assembly")
    body_a = asm.addObject("Part::Feature", "Body")
    body_a.Shape = body

    lid_placed = lid.copy()
    lid_placed.translate(App.Vector(0, 0, P.BODY_H))
    lid_a = asm.addObject("Part::Feature", "Lid")
    lid_a.Shape = lid_placed

    for label, brick in reference_bricks():
        ref = asm.addObject("Part::Feature", f"REF_{label}")
        ref.Shape = brick
        # ViewObject only exists when the GUI is loaded; ignore in headless.
        view = getattr(ref, "ViewObject", None)
        if view is not None:
            try:
                view.Transparency = 70
            except Exception:  # noqa: BLE001
                pass

    asm.recompute()
    asm.saveAs(str(EXPORT_DIR / "telem_enclosure_assembly.FCStd"))
    App.closeDocument(asm.Name)

    print("\nWrote outputs to:", EXPORT_DIR)
    for p in sorted(EXPORT_DIR.iterdir()):
        print("  ", p.name, f"({p.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
