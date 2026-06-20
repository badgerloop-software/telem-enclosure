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
    # 1. Define box covering original bosses at X = 134.6 (overlapping 0.2 mm into the wall)
    boss_box = Part.makeBox(6.0, 85.0, 40.0, App.Vector(134.6 - 0.2, 95.0, 8.0))
    # 2. Extract bosses
    bosses = body.common(boss_box)
    # 3. Cut bosses from the body (which leaves the original wall at X = 134.6 flat)
    body = body.cut(boss_box)
    
    # 4. Move bosses to Face 2
    # The original bosses protrude in +X, centered around Y = 136.17.
    # We want them to protrude in -Y, centered around X = 71.12 on Face 2 (Y=93.98).
    
    # a) Center the bosses at origin (base at X=0, center at Y=0)
    bosses.translate(App.Vector(-134.62, -136.17, 0))
    
    # b) Rotate -90 degrees around Z to point them in -Y
    bosses.rotate(App.Vector(0,0,0), App.Vector(0,0,1), -90)
    
    # c) Translate to Face 2 center (X=71.12, base at Y=93.98)
    bosses.translate(App.Vector(71.12, 93.98, 0))
    
    # 5. Fuse relocated bosses to Face 2
    body = body.fuse(bosses)

    # Patch the 4 small screw holes on the left short wall (X=0, Face 4).
    # Hole centres (Y, Z): (39.8, 18.21), (39.8, 40.21), (61.8, 18.21), (61.8, 40.21)
    # Radius 1.75 mm, depth = full wall thickness = 7.62 mm, axis along +X.
    WALL_THICKNESS = 7.62
    small_hole_plugs = [
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
    body = body.fuse(_fuse(small_hole_plugs))

    # Resize the big hole on the left short wall (X=0, Face 4):
    # Old: dia 21 mm (r=10.5), centre Y=50.8, Z=29.21
    # New: dia 11.5 mm (r=5.75), same centre
    BIG_HOLE_Y = 50.8
    BIG_HOLE_Z = 29.21

    # 1. Plug the existing 21 mm hole with a solid cylinder (r slightly larger to fill fully)
    plug = Part.makeCylinder(10.6, WALL_THICKNESS,
                             App.Vector(0.0, BIG_HOLE_Y, BIG_HOLE_Z),
                             App.Vector(1, 0, 0))
    body = body.fuse(plug)

    # 2. Cut the new 11.5 mm diameter hole through the wall
    new_hole = Part.makeCylinder(5.75, WALL_THICKNESS + 0.2,
                                 App.Vector(-0.1, BIG_HOLE_Y, BIG_HOLE_Z),
                                 App.Vector(1, 0, 0))
    body = body.cut(new_hole)

    # Plug the rectangular cutout on the right short wall (Face 2, X=228.6).
    # Cutout bounds: Y=[93.98, 152.40], Z=[12.70, 22.86], depth into wall from X=220.98 to X=228.60
    rect_plug = Part.makeBox(
        228.60 - 220.98,                 # X depth (exact wall thickness)
        152.40 - 93.98,                  # Y width
        22.86 - 12.70,                   # Z height
        App.Vector(220.98, 93.98, 12.70)
    )
    body = body.fuse(rect_plug)

    # Now drill the 14 missing holes (dia 5.08mm, r=2.54) that should have been
    # there but were removed by the rectangular cutout.
    # Grid: Y in {91.44, 101.60, 111.76, 121.92, 132.08, 142.24, 152.40}
    #       Z in {10.16, 20.32}
    HOLE_R = 2.54
    HOLE_DEPTH = 228.60 - 220.98 + 0.2   # full wall thickness + epsilon each side
    HOLE_X_START = 220.98 - 0.1
    missing_holes = [
        (y, z)
        for y in [91.44, 101.60, 111.76, 121.92, 132.08, 142.24, 152.40]
        for z in [10.16, 20.32]
    ]
    restore_holes = [
        Part.makeCylinder(HOLE_R, HOLE_DEPTH,
                          App.Vector(HOLE_X_START, y, z),
                          App.Vector(1, 0, 0))
        for (y, z) in missing_holes
    ]
    body = body.cut(_fuse(restore_holes))

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
    STEP_Y_INNER   = 93.98     # inner face of left half (thick)
    STEP_Y_OUTER   = 101.60    # outer face of new back of entire enclosure
    CAVITY_X_START = 134.62    # where the thick wall ends and thin wall begins
    THIN_WALL_Y    = 99.06     # inner face of right half (2.54mm thick)
    OLD_BACK_Y     = 223.52    # old deep back of right arm
    EXT_X          = 228.60    # full outer width
    FULL_H         = 50.80     # full body height

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
        STEP_Y_OUTER - THIN_WALL_Y,           # Y: 99.06 → 101.6 (2.54 mm thick)
        FULL_H,
        App.Vector(CAVITY_X_START, THIN_WALL_Y, 0)
    )
    body = body.fuse(right_thin_wall)

    # 3. Bring back the 3 holes on the thin section
    hole_zs = [12.70, 25.40, 38.10]
    holes_to_cut = []
    for z in hole_zs:
        holes_to_cut.append(
            Part.makeCylinder(3.175, 10.0, App.Vector(150.379, 95.0, z), App.Vector(0, 1, 0))
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
    # RESTORE LID SCREW HOLES
    # ═══════════════════════════════════════════════════════════════════════════
    # The back-left and back-right top corner holes were filled in by the back walls.
    # Radius = 2.2225 mm. Let's drill them 15mm deep from the top.
    LID_HOLE_R = 2.2225
    lid_holes = [
        Part.makeCylinder(LID_HOLE_R, 15.0, App.Vector(3.81, 97.79, 51.0), App.Vector(0, 0, -1)),
        Part.makeCylinder(LID_HOLE_R, 15.0, App.Vector(224.79, 97.79, 51.0), App.Vector(0, 0, -1))
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
