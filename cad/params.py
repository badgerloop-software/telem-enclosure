"""Parametric dimensions for the compact telemetry enclosure.

All units are millimetres. Coordinate frame for the body:
    Origin at the OUTER bottom-front-left corner.
    +X = long axis (length)
    +Y = short axis (width)
    +Z = up (toward the lid)

The interior cavity therefore starts at (WALL, WALL, FLOOR) and ends at
(WALL + INT_L, WALL + INT_W, FLOOR + INT_H).

Edit any constant here and re-run `freecadcmd cad/enclosure.py` to regenerate
the model and STEP/STL exports.
"""

# ---------- Internal volume ----------
INT_L = 112.0   # X length, inside
INT_W = 82.0    # Y width, inside
INT_H = 55.0    # Z height, inside (floor top to lid underside)
                # Bumped from 50 → 55 to clear the 18 mm tall Quectel adapter

# ---------- Wall thicknesses ----------
WALL = 2.0      # side walls
FLOOR = 2.5     # bottom plate
LID = 3.0       # lid plate

# ---------- Derived externals ----------
EXT_L = INT_L + 2 * WALL    # 116
EXT_W = INT_W + 2 * WALL    # 86
BODY_H = FLOOR + INT_H      # 52.5 (without lid)
EXT_H = BODY_H + LID        # 55.5

# ---------- Raspberry Pi 4B ----------
PI_L = 85.6
PI_W = 56.5
PI_PCB_T = 1.5

# Pi 4B mounting hole pattern (4 holes, M2.5)
PI_HOLE_DX = 58.0           # along long edge
PI_HOLE_DY = 49.0           # along short edge
PI_HOLE_OFFSET = 3.5        # from each PCB edge to hole center

# Pi standoff geometry
STANDOFF_H = 12.0
STANDOFF_OD = 6.0
STANDOFF_HOLE_D = 2.1       # self-tap pilot for M2.5; use 3.6 for heat-set
STANDOFF_HOLE_DEPTH = 9.0

# Pi placement in the +X / -Y interior corner.
# Local-interior origin is (0,0,0) at the inside floor / front-left.
# Pi long edge along X. Pi short edge against X=INT_L (right short wall).
# Pi media long edge against Y=0 (front long wall).
PI_X0_INT = INT_L - PI_L    # 26.4 (x-coord of Pi's left short edge, inside)
PI_Y0_INT = 0.0             # Pi's media edge flush with front wall
PI_Z0_INT = STANDOFF_H      # Pi PCB bottom Z (above interior floor)

# ---------- Pi 4B I/O port positions (Pi-local, 0,0 at media/USB-C corner) ----------
# Long media edge ports (Pi_y == 0): cutout on the body's Y=0 wall.
PI_USBC_X    = (3.5, 13.0)
PI_HDMI0_X   = (20.0, 32.0)
PI_HDMI1_X   = (36.5, 48.5)
PI_AUDIO_X   = (52.5, 65.0)

# Network short edge ports (Pi_x == PI_L): cutout on the body's X=INT_L wall.
# Pi 4B has Ethernet + 2 USB-A stacks across the full short edge; one
# generous slot covers all three regardless of exact arrangement.
PI_NETPORT_Y = (1.5, 56.0)

# Port heights above PCB top
PI_USBA_H = 17.0
PI_ETH_H = 14.0
PI_HDMI_H = 6.5
PI_USBC_H = 3.5
PI_AUDIO_H = 6.5

# Z reference: top of Pi PCB above the interior floor
PCB_TOP_Z = PI_Z0_INT + PI_PCB_T  # 13.5

# ---------- I/O cutouts (interior coordinates, Z above interior floor) ----------
# Slight clearance around port footprints.
MEDIA_CUTOUT_Z_MIN = PCB_TOP_Z - 1.0    # 12.5
MEDIA_CUTOUT_Z_MAX = PCB_TOP_Z + 8.0    # 21.5
MEDIA_CUTOUT_PAD_X = 1.5                 # extra each side per port group

NET_CUTOUT_Z_MIN = PCB_TOP_Z - 1.0      # 12.5
NET_CUTOUT_Z_MAX = PCB_TOP_Z + 19.0     # 32.5
NET_CUTOUT_Y_PAD = 1.5

# GPIO header pass-through (small wire slot on Y=INT_W wall above the GPIO)
GPIO_PASS_W = 18.0
GPIO_PASS_H = 8.0
GPIO_PASS_Z = PCB_TOP_Z + 2.0           # 15.5
# Centered along X over the GPIO header (GPIO occupies Pi_x ~= 7..58 on Pi 4B)
GPIO_PASS_X_CENTER_INT = PI_X0_INT + 32.5

# ---------- Vent slots ----------
SIDE_VENT_W = 2.0
SIDE_VENT_L = 30.0
SIDE_VENT_COUNT_PER_LONG_WALL = 4
SIDE_VENT_Z_CENTER = 40.0       # near the top of the cavity

LID_VENT_W = 2.0
LID_VENT_L = 20.0
LID_VENT_COUNT = 6

# ---------- Components on the upper layer ----------
RFD_L = 53.0
RFD_W = 33.0
RFD_H = 12.0

# Mini PCIe-to-USB adapter (SUPERPLUS, 3.5" x 1.77" x 0.71")
QU_L = 88.9     # 3.5 inches
QU_W = 44.96    # 1.77 inches
QU_H = 18.03    # 0.71 inches

# Mounting holes: 3.55 mm diameter, M3 self-tap
# Center from each short (L-end) edge: 3 mm + hole_r = 4.775 mm
# Center from each long (W-edge) edge: 2 mm + hole_r = 3.775 mm
QU_HOLE_D = 3.55
QU_HOLE_FROM_L_END = 4.775
QU_HOLE_FROM_W_EDGE = 3.775
QU_MOUNT_POST_OD = 7.0
QU_MOUNT_PILOT_D = 3.1     # M3 self-tap pilot in PETG

RTC_L = 25.0
RTC_W = 22.0
RTC_H = 8.0

# Upper shelf height.  Only the Quectel bay uses a rail now; the RFD900A
# has no mounting holes and is adhesive-mounted directly to the interior
# surface of the left short wall (X=0 inside), so no shelf rail is needed.
SHELF_Z = 32.0
SHELF_RAIL_T = 3.0      # rail thickness (Z) — used only by Quectel bay
SHELF_RAIL_W = 6.0      # rail width (extending from wall inward)

# Quectel bay (back half, near Y=INT_W long wall).
# Start from the left interior wall so the 88.9 mm adapter fits along X.
QU_BAY_X0_INT = 5.0                      # 5 mm from left interior wall
QU_BAY_Y_AT_WALL = INT_W                 # against back long wall
QU_BAY_DEPTH = QU_W + 1.5               # 46.46
QU_BAY_LENGTH = QU_L + 1.5              # 90.4

# Y position of the adapter's near (front) edge in interior coords
QU_Y0_INT = INT_W - QU_W               # 37.04 mm from front

# Adafruit RTC clip-down post (small platform near GPIO)
RTC_X0_INT = 5.0
RTC_Y0_INT = INT_W - RTC_W - 5.0
RTC_PLATFORM_Z = 4.0

# ---------- Lid ----------
LID_LIP_T = 1.5
LID_LIP_DEPTH = 4.0
LID_LIP_GAP = 0.3        # clearance between lip and inside walls

# Antenna holes on the top of the lid
ANT_HOLE_D = 7.0
ANT_LTE_COUNT = 3
ANT_RFD_COUNT = 2
ANT_LTE_SPACING = 16.0
ANT_RFD_SPACING = 18.0
ANT_EDGE_OFFSET_X = 14.0     # from short-edge of lid
ANT_LTE_Y_OFFSET = 18.0      # from front (Y=0) edge of lid
ANT_RFD_Y_OFFSET = EXT_W - 18.0  # from front edge

# Lid screw bosses (corners, M2.5 self-tap into body bosses)
LID_SCREW_INSET = 5.0
LID_SCREW_CLEAR_D = 3.0
LID_SCREW_BOSS_OD = 8.0
LID_SCREW_BOSS_HOLE_D = 2.1   # M2.5 self-tap pilot

# ---------- Tolerances ----------
EPS = 0.01                   # boolean cleanup margin

# ---------- Helper: Pi mounting hole positions ----------
def quectel_hole_positions_interior():
    """Return [(x, y)] of the four Quectel adapter mounting holes
    in interior coordinates.  The adapter sits at (QU_BAY_X0_INT, QU_Y0_INT)
    with L along X and W along Y."""
    x0 = QU_BAY_X0_INT + QU_HOLE_FROM_L_END
    x1 = QU_BAY_X0_INT + QU_L - QU_HOLE_FROM_L_END
    y0 = QU_Y0_INT + QU_HOLE_FROM_W_EDGE
    y1 = QU_Y0_INT + QU_W - QU_HOLE_FROM_W_EDGE
    return [(x0, y0), (x1, y0), (x0, y1), (x1, y1)]


def pi_hole_positions_interior():
    """Return [(x, y)] of the four Pi mounting holes in interior coordinates."""
    x0 = PI_X0_INT + PI_HOLE_OFFSET
    y0 = PI_Y0_INT + PI_HOLE_OFFSET
    return [
        (x0, y0),
        (x0 + PI_HOLE_DX, y0),
        (x0, y0 + PI_HOLE_DY),
        (x0 + PI_HOLE_DX, y0 + PI_HOLE_DY),
    ]


def lid_screw_positions_exterior():
    """Return [(x, y)] of the four lid corner screws in exterior body coords."""
    return [
        (LID_SCREW_INSET, LID_SCREW_INSET),
        (EXT_L - LID_SCREW_INSET, LID_SCREW_INSET),
        (LID_SCREW_INSET, EXT_W - LID_SCREW_INSET),
        (EXT_L - LID_SCREW_INSET, EXT_W - LID_SCREW_INSET),
    ]


def antenna_hole_positions_exterior():
    """Antenna hole centres on the lid (lid lies in body's exterior frame).

    Layout: 3 LTE on the +Y half row, 2 RFD on the -Y half row, both running
    along the X axis with edge offset ANT_EDGE_OFFSET_X from X=0.
    """
    holes = []
    # LTE row (closer to front long wall, Y=ANT_LTE_Y_OFFSET)
    lte_total = (ANT_LTE_COUNT - 1) * ANT_LTE_SPACING
    lte_x0 = (EXT_L - lte_total) / 2.0
    for i in range(ANT_LTE_COUNT):
        holes.append((lte_x0 + i * ANT_LTE_SPACING, ANT_LTE_Y_OFFSET, "LTE"))
    # RFD row (closer to back long wall)
    rfd_total = (ANT_RFD_COUNT - 1) * ANT_RFD_SPACING
    rfd_x0 = (EXT_L - rfd_total) / 2.0
    for i in range(ANT_RFD_COUNT):
        holes.append((rfd_x0 + i * ANT_RFD_SPACING, ANT_RFD_Y_OFFSET, "RFD"))
    return holes
