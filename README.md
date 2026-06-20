# Telemetry Enclosure

![Car 2 enclosure preview](exports/car-2/enclosure_preview.gif)

3D-printable enclosure for an airborne / ground-station telemetry stack:

| Component | Notes |
|-----------|-------|
| Raspberry Pi 4B | Bottom layer, M2.5 standoffs |
| RFD900A telemetry radio | Adhesive-mounted to left interior wall |
| Quectel EG25-G LTE module | 4× M3 wall-boss screws via Mini PCIe-to-USB adapter |
| Adafruit DS3231 RTC | Sits directly on Pi GPIO pins (no separate mount) |

| Version | Dimensions (L × W × H) | Role |
|---------|------------------------|------|
| **car-2** (active) | 228.6 × 223.5 × 57.2 mm | Working redesign — edit these exports |
| **car-1.5** (archive) | 228.6 × 223.5 × 57.2 mm | Pristine recovered SolidWorks 2023 STEP baseline |

Printable in PLA or PETG. See [`exports/README.md`](exports/README.md) for file layout.

---

## Repository layout

```
README.md                        ← you are here
telem-enclosure-components.pdf   ← component datasheets / spec reference
cad/
  import_legacy.py        ← import car-1.5 STEP → exports/car-1.5/
  analyze_step.py         ← inspect bounding boxes and hole sizes
  render_gif.py           ← turntable GIF (arg: car-1.5 or car-2)
  smooth_floor.py         ← car-2 interior floor cleanup (from car-1.5 baseline)
  update_assembly.py      ← rebuild telem_enclosure_assembly.FCStd after body/lid edits
  face_templates.py       ← 1:1 print templates (legacy compact layout)
  enclosure.py / params.py  ← experimental compact parametric model (not current car-2)
  README.md               ← design notes and print settings
exports/
  README.md               ← version layout guide
  car-1.5/                ← recovered SolidWorks archive (do not edit)
  car-2/                  ← active working folder (legacy-based redesign)
viewer/                   ← lightweight STL web viewer (face select, no FreeCAD GUI)
  server.py
  static/                 ← Three.js UI
tools/
  freecad-mcp/          ← contextform/freecad-mcp bridge for Cursor MCP
  render-venv/          ← gitignored Python venv for render_gif.py
  FreeCAD.AppImage      ← gitignored (download separately, see below)
  squashfs-root/        ← gitignored (extracted AppImage runtime)
.cursor/
  mcp.json              ← FreeCAD MCP server config for Cursor
```

## Quick start

1. **Get FreeCAD 1.0+** — either via apt or AppImage:
   ```bash
   sudo apt install freecad          # Ubuntu / Debian
   # or download the AppImage from https://freecad.org/downloads.php
   # and place it at tools/FreeCAD.AppImage
   ```

2. **Regenerate the car-1.5 archive** (only if source STEP files changed):
   ```bash
   echo 'exec(open("cad/import_legacy.py").read())' | \
     ./tools/squashfs-root/usr/bin/freecadcmd
   ```
   Reads `exports/car-1.5/SoftwareEnclosure*Car1.5.STEP`, aligns the body to
   origin, and writes `enclosure_body.{FCStd,step,stl}`, `enclosure_lid.*`, and
   `telem_enclosure_assembly.FCStd` into `exports/car-1.5/`.

3. **Work in `exports/car-2/`** — the active redesign. Copy fresh exports from
   `car-1.5/` when resetting, then edit `enclosure_body.{FCStd,step,stl}` (and lid
   as needed) in FreeCAD GUI or via the MCP bridge below.

4. **Regenerate the README preview GIF** after car-2 changes:
   ```bash
   tools/render-venv/bin/python cad/render_gif.py car-2
   ```

5. **Sync the FreeCAD assembly** after body or lid STEP/STL changes:
   ```bash
   ./tools/squashfs-root/usr/bin/freecadcmd cad/update_assembly.py car-2
   ```

See [`cad/README.md`](cad/README.md) for design notes and print settings.

## Web viewer (STL + face IDs)

A lightweight browser viewer lives in [`viewer/`](viewer/) — useful for inspecting
exports without opening FreeCAD.

```bash
python3 viewer/server.py
# open http://127.0.0.1:8765
```

| Feature | Notes |
|---------|--------|
| Model picker | All `exports/**/*.stl` (defaults to `car-2/enclosure_body.stl`) |
| Auto-reload | Polls file mtime every 1.5 s when STL on disk changes |
| Face IDs | First click on a flat patch assigns **#1, #2, …**; reuse when re-selected |
| Orientation | Body sits on its bottom face; **+X / +Y / +Z** axis labels on the grid |
| Save | Writes binary STL back to `exports/` (creates `.bak` first) |

**Regenerate body exports** (smooth interior floor, etc.):

```bash
./tools/squashfs-root/usr/bin/freecadcmd cad/smooth_floor.py
./tools/squashfs-root/usr/bin/freecadcmd cad/update_assembly.py car-2
```

The viewer reloads automatically when `enclosure_body.stl` changes.

## Working with Cursor AI

Use the viewer and chat together so you can point at geometry by name:

1. **Start the viewer** (`python3 viewer/server.py`) and open the car-2 body STL.
2. **Click faces** in the model — each gets a stable number in the sidebar (e.g. **Face #2**).
3. **Tell the agent** what to change using those IDs: *“smooth face #2”*, *“remove bosses above face #3”*, etc.
4. The agent edits CAD scripts (e.g. `cad/smooth_floor.py`) or drives **FreeCAD MCP** (below), re-exports STEP/STL, and the viewer picks up the new mesh.

For live boolean edits in FreeCAD GUI, use the MCP bridge. For quick visual review and
face naming, use the web viewer — no FreeCAD window required.

## Cursor MCP (drive FreeCAD from chat)

The repo ships a `.cursor/mcp.json` pointing to the bundled `freecad-mcp` bridge.

1. Install the Python `mcp` package (already done if you cloned this repo with the venv):
   ```bash
   cd tools/freecad-mcp && python3 -m venv .venv && .venv/bin/pip install mcp
   ```
2. In Cursor: **Settings → MCP → reload** — a `freecad` server should appear.
3. Launch FreeCAD GUI, open `exports/car-2/enclosure_body.FCStd` or `enclosure_lid.FCStd`,
   then ask the agent to make changes; it drives FreeCAD live over the Unix socket.

## Printing

| | Body | Lid |
|---|---|---|
| Material | PETG (preferred) or PLA | PETG or PLA |
| Layer height | 0.2 mm | 0.2 mm |
| Infill | 20% gyroid | 20% gyroid |
| Walls | 3 perimeters | 3 perimeters |
| Supports | Tree — I/O cutouts only | None |
| Orientation | Open side up | Top face down |

Use M2.5 brass heat-set inserts in the Pi standoffs and lid-corner screw bosses  
for reusability. M3 × 6 mm self-tappers secure the Quectel adapter to its posts.
