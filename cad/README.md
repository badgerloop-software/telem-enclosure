# Compact Telemetry Enclosure

Parametric 3D-printable enclosure for:

- Raspberry Pi 4B
- RFD900A telemetry radio
- Quectel EG25-G LTE module (USB)
- Adafruit RTC (CR1220 onboard)

All dimensions in `cad/params.py`. The build script `cad/enclosure.py`
generates two STEP + STL files (body and lid) and an assembly preview into
`exports/`.

## Layout

```
                   +Y (back, long wall)
                   +-----------------------------+
                   | [GPIO pass-through]         |
                   |     Quectel rail + posts    |
                   |   ___________________       |
                   |  |                   |      |
    RFD900A (VHB)  |  |  Pi 4B (corner)   | Eth/ |
    on left wall → |  |  long edge along  | USB  |  +X
                   |  |  X axis           |      |
                   |  |___________________|      |
                   |                             |
                   | RTC                         |
                   +-----------------------------+
                   -Y (front long wall, HDMI/USB-C/audio cutout)
                                     |
                                  +X end (Eth + 2x USB-A cutout)
```

The Raspberry Pi sits in the +X / -Y interior corner so two of its I/O edges
are flush against the body walls.

### RFD900A mounting

The RFD900A (53 × 33 × 12 mm) has no PCB mounting holes, so it is
**adhesive-mounted** to the flat interior face of the left short wall (X = 0
inside), using VHB or double-sided foam tape. The model has no structural
features for it — the interior wall face is left smooth. Orient the board
with its antenna connectors toward the lid and U.FL cables routed up through
the lid antenna holes.

## Dimensions (default)

| Quantity              | Value      |
| --------------------- | ---------- |
| Internal cavity       | 112 x 82 x 50 mm |
| External (body+lid)   | 116 x 86 x ~55.5 mm |
| Wall thickness        | 2.0 mm     |
| Floor thickness       | 2.5 mm     |
| Lid thickness         | 3.0 mm     |
| Pi standoff height    | 12 mm (M2.5 self-tap) |
| Upper shelf height    | 36 mm above interior floor |
| Antenna holes         | 5 x diameter 7.0 mm (3 LTE + 2 RFD) |
| Lid corner screws     | 4 x M2.5 self-tap |

> The original spec called external height of 54.5 mm. Since wall=2, floor=2.5
> and lid=3, total external height with a flush lid is `2.5 + 50 + 3 = 55.5 mm`.
> Adjust `INT_H`, `FLOOR`, or `LID` in `params.py` if you need exactly 54.5 mm.

## Generate the model

Requires FreeCAD 1.0 or later (provides `freecadcmd` and the `Part`/`Mesh`
Python modules).

```bash
freecadcmd cad/enclosure.py
```

This writes into `exports/`:

- `enclosure_body.FCStd` / `.step` / `.stl`
- `enclosure_lid.FCStd`  / `.step` / `.stl`
- `telem_enclosure_assembly.FCStd` (body + lid + transparent reference bricks
  for Pi, RFD900A, Quectel, RTC)

If you only have the FreeCAD AppImage extracted at `tools/FreeCAD.AppImage`:

```bash
./tools/FreeCAD.AppImage --console cad/enclosure.py
# or, if extracted:
./tools/squashfs-root/AppRun --console cad/enclosure.py
```

## Driving FreeCAD from Cursor (MCP)

The repo ships `.cursor/mcp.json` configured for the
[contextform/freecad-mcp](https://github.com/contextform/freecad-mcp) bridge.
Once installed at `~/tools/freecad-mcp/` you can describe changes in chat and
the agent will manipulate the live FreeCAD document over MCP. The parametric
script remains the source of truth for regenerating from scratch.

## Print settings

| Setting   | Body                    | Lid                       |
| --------- | ----------------------- | ------------------------- |
| Material  | PETG (preferred) / PLA  | PETG / PLA                |
| Layer     | 0.2 mm                  | 0.2 mm                    |
| Infill    | 20% gyroid              | 20% gyroid                |
| Walls     | 3 perimeters            | 3 perimeters              |
| Supports  | Tree, only for I/O wall cutouts and standoff overhang | None (print snap-lip-down) |
| Orient    | Open side up            | Top face down             |

Use M2.5 brass heat-set inserts in the standoffs and screw bosses for
reusability; if you don't have inserts, the default 2.1 mm pilot holes are
sized for M2.5 self-tappers in PETG.

## Tweaking the design

Common edits, all in `cad/params.py`:

- Change overall size: `INT_L`, `INT_W`, `INT_H`.
- Move the Pi off the corner: edit `PI_X0_INT`, `PI_Y0_INT`.
- Swap antenna group orientation: edit `ANT_LTE_Y_OFFSET`, `ANT_RFD_Y_OFFSET`,
  spacings or counts.
- Wider GPIO pass-through: `GPIO_PASS_W`, `GPIO_PASS_H`.
- More vent slots: `SIDE_VENT_COUNT_PER_LONG_WALL`, `LID_VENT_COUNT`.

Re-run `freecadcmd cad/enclosure.py`. The script also prints a clearance
report and warns if any component would collide with the lid or shelves.

## Component — Quectel adapter (Mini PCIe-to-USB)

SUPERPLUS adapter, actual dimensions: **88.9 × 44.96 × 18.03 mm**

4 mounting holes (3.55 mm Ø):
- Centre from each short (L-end) edge: 4.775 mm
- Centre from each long (W-edge) edge: 3.775 mm

The enclosure has 4 × M3 self-tap screw posts at these positions on the upper
shelf. The adapter rests on the posts and is secured with M3 × 6 mm screws.

## Verified clearances (from current params)

The build script prints a clearance report each run. Current numbers:

| Item                                | Z (world, mm) | Headroom (mm) |
| ----------------------------------- | ------------- | ------------- |
| Pi USB-A stack top                  | 33.0          | —             |
| Shelf rail bottom                   | 34.5          | 1.5 above Pi  |
| RFD900A top (on shelf)              | 49.5          | 8.0 to lid    |
| Quectel adapter top (on shelf)      | 55.5          | 2.0 to lid    |
| RFD900A vs Quectel side gap         | —             | 4.0 mm        |

`INT_H` is 55 mm (external body height ≈ 60.5 mm including floor + lid). If
your Quectel adapter ends up taller than 18 mm, increase `INT_H` by the
difference and rebuild.

## Known limitations / future work

- Component bays use simple side rails + a 4 mm retention nib; for shipping
  use, replace with screw-mount posts to whatever holes the RFD900A and
  Quectel adapter actually expose.
- Antenna hole layout is symmetric/centered; if specific antennas need to
  avoid the lid stiffener ribs, override coordinates in
  `antenna_hole_positions_exterior()`.
- GPIO access is via lid removal plus a single 18x8 mm pass-through slot on
  the back long wall. For a real panel-mount GPIO breakout, add a dedicated
  ribbon-cable cutout on the back long wall in `params.py`.
- Lid screw bosses hang from the top of the body walls (not from the floor),
  so they clear the Pi PCB sitting in the corner. They give ~10 mm of M2.5
  thread engagement.
