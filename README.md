# Compact Telemetry Enclosure

3D-printable enclosure for a compact airborne / ground-station telemetry stack:

| Component | Notes |
|-----------|-------|
| Raspberry Pi 4B | Bottom layer, M2.5 standoffs |
| RFD900A telemetry radio | Adhesive-mounted to left interior wall |
| Quectel EG25-G LTE module | On upper shelf, 4× M3 screws via Mini PCIe adapter |
| Adafruit DS3231 RTC | Clip-down platform near GPIO header |

External dimensions: **116 × 86 × 60.5 mm** (L × W × H, body + lid)  
Printable in PLA or PETG, no supports required except for I/O wall cutouts.

---

## Repository layout

```
README.md               ← you are here
cad/
  params.py             ← all dimensions as named constants
  enclosure.py          ← FreeCAD Python build script
  README.md             ← detailed design notes, print settings, clearance table
exports/
  enclosure_body.step / .stl
  enclosure_lid.step   / .stl
  telem_enclosure_assembly.FCStd   (body + lid + reference bricks in FreeCAD)
tools/
  freecad-mcp/          ← contextform/freecad-mcp bridge for Cursor MCP
  FreeCAD.AppImage      ← gitignored (download separately, see below)
  squashfs-root/        ← gitignored (extracted AppImage runtime)
.cursor/
  mcp.json              ← FreeCAD MCP server config for Cursor
```

## Quick start — regenerate the model

1. **Get FreeCAD 1.0+** — either via apt or AppImage:
   ```bash
   sudo apt install freecad          # Ubuntu / Debian
   # or download the AppImage from https://freecad.org/downloads.php
   # and place it at tools/FreeCAD.AppImage
   ```

2. **Run the build script:**
   ```bash
   freecadcmd cad/enclosure.py
   # or, using the local AppImage:
   echo 'exec(open("cad/enclosure.py").read())' | \
     ./tools/squashfs-root/usr/bin/freecadcmd
   ```
   This writes `exports/enclosure_body.{step,stl}`, `exports/enclosure_lid.{step,stl}`,  
   and `exports/telem_enclosure_assembly.FCStd`, and prints a clearance report.

3. **Tweak dimensions** in [`cad/params.py`](cad/params.py) and re-run step 2.

See [`cad/README.md`](cad/README.md) for full design notes, a component clearance  
table, mounting hole specs, and print settings.

## Cursor MCP (drive FreeCAD from chat)

The repo ships a `.cursor/mcp.json` pointing to the bundled `freecad-mcp` bridge.

1. Install the Python `mcp` package (already done if you cloned this repo with the venv):
   ```bash
   cd tools/freecad-mcp && python3 -m venv .venv && .venv/bin/pip install mcp
   ```
2. In Cursor: **Settings → MCP → reload** — a `freecad` server should appear.
3. Launch FreeCAD GUI, then ask the agent to make changes; it drives FreeCAD live  
   over the Unix socket while `cad/params.py` remains the source of truth.

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
