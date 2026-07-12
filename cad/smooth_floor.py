"""Smooth the car-2 interior floor: remove square pockets and Pi standoff bosses.

Run from project root:

    ./tools/squashfs-root/usr/bin/freecadcmd cad/smooth_floor.py

Reads  exports/car-1.5/enclosure_body.step  (pristine baseline)
Writes exports/car-2/enclosure_body.{FCStd,step,stl}
"""

from __future__ import annotations

import sys
from pathlib import Path

import FreeCAD as App
import Mesh
import Part

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SRC = ROOT / "exports" / "car-1.5" / "enclosure_body.step"
EXPORT = ROOT / "exports" / "car-2"
FLOOR = 7.62
CUT_TOP = 13.5
PI = [(163.6, 94.7), (163.6, 152.4), (212.1, 94.7), (212.1, 152.4)]

# Interior floor footprint (from aligned legacy body)
INT_X0 = 7.62
INT_Y0 = 7.62
INT_L = 213.4
INT_W = 213.4


def _fuse(boxes):
    shape = boxes[0]
    for b in boxes[1:]:
        shape = shape.fuse(b)
    return shape


def build_smooth_body() -> Part.Shape:
    body = Part.read(str(SRC))
    vol0 = body.Volume

    # Extract LTE bosses BEFORE increasing height, so they don't get stretched!
    boss_box = Part.makeBox(6.0, 85.0, 40.0, App.Vector(134.6 - 0.2, 95.0, 8.0))
    bosses = body.common(boss_box)
    body = body.cut(boss_box)

    # INCREASE ENCLOSURE HEIGHT BY 10mm
    # Slice the original body at Z=45.0, extrude the cross section by 10mm, and lift the top half.
    # This preserves all holes below Z=45 and the complex lip structure above Z=47.
    cut_box_top = Part.makeBox(500, 500, 100, App.Vector(-100, -100, 45.0))
    bottom_half = body.cut(cut_box_top)
    top_half = body.common(cut_box_top)
    
    z45_faces = []
    for f in bottom_half.Faces:
        bb = f.BoundBox
        if abs(bb.ZMin - 45.0) < 1e-3 and abs(bb.ZMax - 45.0) < 1e-3:
            z45_faces.append(f)
            
    if z45_faces:
        middle_section = z45_faces[0].extrude(App.Vector(0,0,10.0))
        for f in z45_faces[1:]:
            middle_section = middle_section.fuse(f.extrude(App.Vector(0,0,10.0)))
        top_half.translate(App.Vector(0, 0, 10.0))
        body = bottom_half.fuse(middle_section).fuse(top_half)
        body = body.removeSplitter()

    cutters = [
        # Square walled pockets (expanded 1 mm to catch thin rims)
        Part.makeBox(59.2, 49.5, CUT_TOP - FLOOR + 1.0, App.Vector(62.5, 41.3, FLOOR)),
        Part.makeBox(38.8, 66.8, CUT_TOP - FLOOR + 1.0, App.Vector(157.8, 11.7, FLOOR)),
    ]

    # Pi standoff bosses above the interior floor
    for cx, cy in PI:
        cutters.append(
            Part.makeBox(
                6.5,
                6.5,
                CUT_TOP - FLOOR + 1.0,
                App.Vector(cx - 3.25, cy - 3.25, FLOOR),
            )
        )

    body = body.cut(_fuse(cutters))

    # Raise the two sunken pocket floors flush with the main interior floor (Z=7.621).
    # The original pockets left coplanar islands at Z=7.221, 0.4 mm below the main floor.
    pocket_fillers = [
        # Pocket 1: X=[62, 122], Y=[41, 91] (expanded to overlap existing walls)
        Part.makeBox(62.0, 52.0, 0.40, App.Vector(61.0, 40.0, 7.220)),
        # Pocket 2: X=[157, 197], Y=[11, 79] (expanded)
        Part.makeBox(42.0, 70.0, 0.40, App.Vector(156.0, 10.0, 7.220)),
    ]
    body = body.fuse(_fuse(pocket_fillers))

    # Fill Pi through-holes so the interior floor is flat (no open bores)
    pi_hole_fillers = [
        Part.makeCylinder(2.0, FLOOR, App.Vector(cx, cy, 0.0), App.Vector(0, 0, 1))
        for cx, cy in PI
    ]
    body = body.fuse(_fuse(pi_hole_fillers))

    # Relocate LTE adapter screw bosses from outer wall X=134.6 to Face 2 (Y=93.98)
    # (Bosses were already extracted at the beginning of the script to prevent stretching)
    
    # 4. Move bosses to Face 2
    # The original bosses protrude in +X, centered around Y = 136.17.
    # We want them to protrude in -Y, centered around X = 71.12 on Face 2 (Y=93.98).
    
    # a) Center the bosses at origin (base at X=0, center at Y=0)
    bosses.translate(App.Vector(-134.62, -136.17, 0))
    
    # b) Rotate -90 degrees around Z to point them in -Y
    bosses.rotate(App.Vector(0,0,0), App.Vector(0,0,1), -90)
    
    # c) Translate to Face 2 center (X=61.12, base at Y=98.60)
    # Shifted left by 10mm to avoid the floor hole at X=13.97
    bosses.translate(App.Vector(61.12, 98.60, 0))
    
    # 5. (Bosses will be fused later, after the back wall is hollowed out)

    # ═══════════════════════════════════════════════════════════════════════════
    # WALL FEATURE SWAP: holes/cutouts moved to opposing short walls
    #   Original:  Left wall (X=0)   had 4 small screw holes + 1 dia-11.5mm hole
    #              Right wall (X=228.6) had 14-hole grid (dia 5.08mm) + rect plug
    #   After swap: each wall gets the other's features.
    # ═══════════════════════════════════════════════════════════════════════════
    WALL_THICKNESS = 7.62
    RIGHT_WALL_X   = 228.60
    RIGHT_WALL_X_INNER = 220.98   # X=228.60 - 7.62

    # (Left wall cuts have been moved later in the script to ensure plugs are applied first)

    # ── Right wall (X=228.6): seal the grid holes with a solid box fill ───────
    # Use a box that covers the entire region containing the grid holes so there
    # is no risk of FreeCAD's boolean kernel leaving thin residual surfaces.
    # Grid bounding box on the right wall:
    #   Y: 10.16 - 2.54 = 7.62  →  101.60 + 2.54 = 104.14
    #   Z: 10.16 - 2.54 = 7.62  →  40.64 + 2.54 = 43.18
    grid_patch = Part.makeBox(
        RIGHT_WALL_X - RIGHT_WALL_X_INNER + 0.2,       # full wall thickness + epsilon
        104.14 - 7.62,                                 # Y span: 96.52 mm
        43.18 - 7.62,                                  # Z span: 35.56 mm
        App.Vector(RIGHT_WALL_X_INNER - 0.1, 7.62, 7.62)
    )
    body = body.fuse(grid_patch)

    # Also plug the rectangular cutout on the right wall (original baseline remnant).
    # Cutout bounds: Y=[93.98, 152.40], Z=[12.70, 22.86]
    rect_plug = Part.makeBox(
        RIGHT_WALL_X - RIGHT_WALL_X_INNER,   # X depth = wall thickness
        152.40 - 93.98,                       # Y width
        22.86 - 12.70,                        # Z height
        App.Vector(RIGHT_WALL_X_INNER, 93.98, 12.70)
    )
    body = body.fuse(rect_plug)

    # Removed code that drilled 4 small screw holes into the RIGHT wall.
    # Re-drill the big hole on the right wall
    # User requested to ensure this hole is perfectly centered on the right wall (Y and Z).
    BIG_HOLE_Y = 101.60 / 2.0
    BIG_HOLE_Z = 60.80 / 2.0  # Center of new 60.80 height
    big_hole_right = Part.makeCylinder(
        5.75, RIGHT_WALL_X - RIGHT_WALL_X_INNER + 0.2,
        App.Vector(RIGHT_WALL_X_INNER - 0.1, BIG_HOLE_Y, BIG_HOLE_Z),
        App.Vector(1, 0, 0)
    )
    body = body.cut(big_hole_right)

    # Patch the 4 small screw holes originally on the left wall.
    left_small_plugs = [
        Part.makeCylinder(1.75 + 0.05, WALL_THICKNESS,
                          App.Vector(0.0, cy, cz),
                          App.Vector(1, 0, 0))
        for (cy, cz) in [
            (39.8, 18.21),
            (39.8, 40.21),
            (61.8, 18.21),
            (61.8, 40.21),
        ]
    ]
    body = body.fuse(_fuse(left_small_plugs))

    # Patch the two 1-inch holes on the front wall
    front_plugs = [
        Part.makeCylinder(12.7 + 0.1, WALL_THICKNESS + 0.2, App.Vector(cx, -0.1, 25.4), App.Vector(0, 1, 0))
        for cx in [29.21, 72.39]
    ]
    body = body.fuse(_fuse(front_plugs))

    # Plug the original big 21mm hole on the left wall and leave no new hole.
    # Old: dia 21 mm (r=10.5), centre Y=50.8, Z=29.21
    left_big_plug = Part.makeCylinder(10.6, WALL_THICKNESS,
                                      App.Vector(0.0, 50.8, 29.21),
                                      App.Vector(1, 0, 0))
    body = body.fuse(left_big_plug)

    # Now that the left wall is fully plugged and solid, we drill the two new large side-by-side holes.
    # Left hole (higher Y): 27 mm diameter (r=13.5). Center Y = 67.7
    # Right hole (lower Y): 30 mm diameter (r=15.0). Center Y = 33.8
    # Vertically centered on the new 60.80mm wall height
    left_big_hole = Part.makeCylinder(13.5, WALL_THICKNESS + 0.2,
                                      App.Vector(-0.1, 67.7, 60.80 / 2.0),
                                      App.Vector(1, 0, 0))
    right_big_hole = Part.makeCylinder(15.0, WALL_THICKNESS + 0.2,
                                       App.Vector(-0.1, 33.8, 60.80 / 2.0),
                                       App.Vector(1, 0, 0))
    body = body.cut(left_big_hole)
    body = body.cut(right_big_hole)

    # ═══════════════════════════════════════════════════════════════════════════
    # CONVERT L-SHAPE TO COMPACT I-SHAPE (reduce footprint)
    #
    # Strategy:
    #   1. Cut away the right arm's deep portion (Y=[101.6→223.52])
    #   2. Extend the left half's thick wall (Y=93.98) slightly to X=134.62
    #      (to perfectly bound the LTE area if it wasn't already).
    #   3. For the right half (X=[134.62, 228.6]), add a thinner wall at Y=99.06.
    #   4. Re-drill the 3 holes originally at X=150.379 into the thinner right wall.
    #   5. Fix floor holes: add a matching back-right corner hole at (214.63, 87.63).
    # ═══════════════════════════════════════════════════════════════════════════
    STEP_Y_INNER   = 98.60     # inner face of left half (thick, moved back for 3mm wall)
    STEP_Y_OUTER   = 101.60    # outer face of new back of entire enclosure
    CAVITY_X_START = 134.62    # where the thick wall ends and thin wall begins
    THIN_WALL_Y    = 98.60     # inner face of right half (now 3.0mm thick, matching left half)
    OLD_BACK_Y     = 223.52    # old deep back of right arm
    EXT_X          = 228.60    # full outer width
    FULL_H         = 60.80     # full body height (increased by 10mm)

    # 1. Remove the right arm's deep portion
    right_arm_cut = Part.makeBox(
        EXT_X + 0.2,
        OLD_BACK_Y - STEP_Y_OUTER + 0.2,
        FULL_H + 0.2,
        App.Vector(-0.1, STEP_Y_OUTER - 0.1, -0.1)
    )
    body = body.cut(right_arm_cut)

    # 2. Add the back walls
    # A) Thick wall up to CAVITY_X_START (just in case the original left arm X max was 127)
    left_thick_wall = Part.makeBox(
        CAVITY_X_START,                       # X: 0 → 134.62
        STEP_Y_OUTER - STEP_Y_INNER,           # Y: 93.98 → 101.6
        FULL_H,
        App.Vector(0, STEP_Y_INNER, 0)
    )
    body = body.fuse(left_thick_wall)

    # B) Thin wall for the right half
    right_thin_wall = Part.makeBox(
        EXT_X - CAVITY_X_START,               # X: 134.62 → 228.6
        STEP_Y_OUTER - THIN_WALL_Y,           # Y: 98.60 → 101.6 (3.0 mm thick)
        FULL_H,
        App.Vector(CAVITY_X_START, THIN_WALL_Y, 0)
    )
    body = body.fuse(right_thin_wall)

    # 3. Bring back the 3 antenna holes on the thin section
    # Shifted left by 10mm (from 150.379 to 140.379) to maintain exact distance from LTE bosses
    hole_zs = [12.70, 25.40, 38.10]
    holes_to_cut = []
    for z in hole_zs:
        holes_to_cut.append(
            Part.makeCylinder(3.175, 10.0, App.Vector(140.379, 95.0, z), App.Vector(0, 1, 0))
        )
    body = body.cut(_fuse(holes_to_cut))

    # 4. Floor hole fix.
    #    The cut at Y>101.6 automatically removes the deep holes at Y=214.63.
    #    Existing holes after cut:
    #      (13.97, 13.97)  front-left  ✓
    #      (214.63, 13.97) front-right ✓
    #      (13.97, 87.63)  back-left   ✓  (inside left arm, close to new back wall)
    #    Missing: back-right corner → drill (214.63, 87.63)
    FHOLE_R = 3.1115
    FHOLE_D = 7.62 + 0.2    # floor thickness + epsilon

    body = body.cut(Part.makeCylinder(
        FHOLE_R, FHOLE_D,
        App.Vector(214.63, 87.63, -0.1),
        App.Vector(0, 0, 1)
    ))

    # ═══════════════════════════════════════════════════════════════════════════
    # RFD900A RADIO MOUNT (Right half thin wall)
    # ═══════════════════════════════════════════════════════════════════════════
    # Dimensions: 33 mm (H) x 53 mm (L) x 9.5 mm (W)
    # It slides in upright resting on its thin edge (base is 53 x 9.5),
    # with the antenna threads sticking out the back wall.
    RADIO_W = 9.5
    RADIO_L = 53.0
    RADIO_H = 33.0
    RADIO_X_CENTER = 195.0   # Shifted left 10 mm to expose back-right floor hole at X=214.63
    GUIDE_T = 2.0    # Thickness of the vertical guide walls
    # Guide walls only cover the back half of the module length so the LED
    # at the front end remains visible and the antenna connectors are already
    # exposed by the cutout in the back wall.
    GUIDE_L = RADIO_L / 2.0   # ~26.5 mm — half the module length

    radio_z_bottom = 7.62
    radio_y_back = THIN_WALL_Y     # 99.06
    radio_y_front = radio_y_back - RADIO_L  # 46.06
    # Shortened guide walls start at the back wall and only extend half-way
    radio_guide_y_start = radio_y_back - GUIDE_L

    # Left guide wall (back half only)
    left_guide = Part.makeBox(
        GUIDE_T,
        GUIDE_L,
        RADIO_H,
        App.Vector(RADIO_X_CENTER - RADIO_W/2 - GUIDE_T, radio_guide_y_start, radio_z_bottom)
    )
    body = body.fuse(left_guide)

    # Right guide wall (back half only)
    right_guide = Part.makeBox(
        GUIDE_T,
        GUIDE_L,
        RADIO_H,
        App.Vector(RADIO_X_CENTER + RADIO_W/2, radio_guide_y_start, radio_z_bottom)
    )
    body = body.fuse(right_guide)
    
    # Cutout on the back wall for the antenna threads
    antenna_cutout = Part.makeBox(
        RADIO_W,
        STEP_Y_OUTER - THIN_WALL_Y + 0.2,   # Through the 2.54mm thin wall + epsilon
        RADIO_H,
        App.Vector(RADIO_X_CENTER - RADIO_W/2, THIN_WALL_Y - 0.1, radio_z_bottom)
    )
    body = body.cut(antenna_cutout)

    # ═══════════════════════════════════════════════════════════════════════════
    # RASPBERRY PI 4 MOUNTING HOLES
    # ═══════════════════════════════════════════════════════════════════════════
    # Pi 4 footprint: 85 x 56 mm. Hole pattern: 58 x 49 mm.
    # Placed close to the front wall (Y=7.62 inner), and between the LTE bosses and radio.
    # Pi PCB starts at X=110.0 to clear LTE boss at X=107.6, ending at X=195.0 to clear radio at X=198.25.
    PI_BOSS_R_OUTER = 3.175
    PI_BOSS_R_INNER = 1.753
    PI_BOSS_Z_TOP = 12.70
    
    pi_x1 = 110.0 + 3.5     # 113.5
    pi_x2 = pi_x1 + 58.0    # 171.5
    pi_y1 = 7.62 + 1.0 + 3.5 # 12.12 (1mm clearance from front wall + 3.5mm inset)
    pi_y2 = pi_y1 + 49.0    # 61.12
    
    pi_bosses = []
    pi_inner_holes = []
    for x in [pi_x1, pi_x2]:
        for y in [pi_y1, pi_y2]:
            # Add the solid boss cylinder from the floor up to Z=12.70
            pi_bosses.append(
                Part.makeCylinder(PI_BOSS_R_OUTER, PI_BOSS_Z_TOP - 7.62, App.Vector(x, y, 7.62), App.Vector(0, 0, 1))
            )
            # Add the inner hole cutting into the boss and partially into the floor (stop at Z=3.0 so it doesn't pierce the bottom)
            pi_inner_holes.append(
                Part.makeCylinder(PI_BOSS_R_INNER, PI_BOSS_Z_TOP - 3.0 + 0.2, App.Vector(x, y, 3.0), App.Vector(0, 0, 1))
            )
            
    body = body.fuse(_fuse(pi_bosses))
    body = body.cut(_fuse(pi_inner_holes))

    # ═══════════════════════════════════════════════════════════════════════════
    # THIN OUT WALLS (LEFT, FRONT, RIGHT) TO 3.0mm
    # ═══════════════════════════════════════════════════════════════════════════
    # We cut inner pockets from Z=7.62 (floor) to Z=61.0.
    # The original walls are 7.62mm thick. We expand the cavity outward.
    # We leave 7.62 x 7.62 mm bosses at the 4 corners for the lid screw holes.
    
    Z_START = 7.62
    Z_H = 61.0 - 7.62
    NEW_WALL_T = 3.0
    
    # 1. Left wall inner cut (X: 3.0 -> 8.0)
    left_thin_cut = Part.makeBox(
        8.0 - NEW_WALL_T,        # X width: 5.0
        93.98 - 7.62,            # Y length: 86.36
        Z_H,                     # Z height
        App.Vector(NEW_WALL_T, 7.62, Z_START)
    )
    body = body.cut(left_thin_cut)
    
    # 2. Right wall inner cut (X: 220.0 -> 225.60)
    right_thin_cut = Part.makeBox(
        (228.60 - NEW_WALL_T) - 220.0,  # X width: 5.60
        93.98 - 7.62,            # Y length: 86.36
        Z_H,                     # Z height
        App.Vector(220.0, 7.62, Z_START)
    )
    body = body.cut(right_thin_cut)
    
    # 3. Front wall inner cut (Y: 3.0 -> 8.0)
    front_thin_cut = Part.makeBox(
        220.98 - 7.62,           # X length: 213.36
        8.0 - NEW_WALL_T,        # Y width: 5.0
        Z_H,                     # Z height
        App.Vector(7.62, NEW_WALL_T, Z_START)
    )
    body = body.cut(front_thin_cut)

    # 4. Back wall (left half) inner cut (Y: 93.98 -> 98.60)
    # The original left-half back wall was at Y=93.98. We push it back to 98.60 (3mm thick).
    # We leave X=0..7.62 alone to preserve the back-left corner boss.
    back_thin_cut = Part.makeBox(
        134.62 - 7.62,             # X length: 127.0
        98.60 - 93.98,             # Y width: 4.62
        Z_H,                       # Z height
        App.Vector(7.62, 93.98, Z_START)
    )
    body = body.cut(back_thin_cut)

    # Now that the back wall is thinned, fuse the relocated LTE bosses to it
    body = body.fuse(bosses)

    # ═══════════════════════════════════════════════════════════════════════════
    # RESTORE LID SCREW HOLES
    # ═══════════════════════════════════════════════════════════════════════════
    # The back-left and back-right top corner holes were filled in by the back walls.
    # Radius = 2.2225 mm. Let's drill them 15mm deep from the top.
    LID_HOLE_R = 2.2225
    lid_holes = [
        Part.makeCylinder(LID_HOLE_R, 15.0, App.Vector(3.81, 97.79, 61.0), App.Vector(0, 0, -1)),
        Part.makeCylinder(LID_HOLE_R, 15.0, App.Vector(224.79, 97.79, 61.0), App.Vector(0, 0, -1))
    ]
    body = body.cut(_fuse(lid_holes))

    try:
        body = Part.refineShape(body)
    except Exception:
        pass
    body = body.removeSplitter()

    print(f"Volume {vol0:.0f} -> {body.Volume:.0f} mm³ (removed {vol0 - body.Volume:.0f})")
    return body



def save_exports(body: Part.Shape) -> None:
    EXPORT.mkdir(parents=True, exist_ok=True)
    doc = App.newDocument("enclosure_body")
    obj = doc.addObject("Part::Feature", "Body")
    obj.Shape = body
    doc.recompute()
    doc.saveAs(str(EXPORT / "enclosure_body.FCStd"))
    body.exportStep(str(EXPORT / "enclosure_body.step"))
    mesh = Mesh.Mesh()
    mesh.addFacets(body.tessellate(0.1))
    mesh.write(str(EXPORT / "enclosure_body.stl"))
    App.closeDocument(doc.Name)
    print("Wrote exports/car-2/enclosure_body.{FCStd,step,stl}")


def main() -> None:
    if not SRC.exists():
        print(f"Missing baseline: {SRC}", file=sys.stderr)
        sys.exit(1)
    save_exports(build_smooth_body())


main()
