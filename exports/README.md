# Exports by car version

All generated model files are grouped by vehicle generation.

## `car-2/` — active redesign (work here)

| File | Description |
|------|-------------|
| `enclosure_body.{FCStd,step,stl}` | Body — legacy car-1.5 geometry with redesign edits |
| `enclosure_lid.{FCStd,step,stl}` | Lid copied from car-1.5 baseline |
| `telem_enclosure_assembly.FCStd` | Body + lid preview |
| `enclosure_preview.gif` | Turntable animation (shown in root README) |
| `face_templates.pdf` | Legacy 1:1 fit-check sheets (compact parametric layout; may not match) |

**Extents:** 228.6 × 223.5 × 57.2 mm (body + lid)

**Current edits:** interior floor smoothed — rectangular cutouts removed, circular Pi
mounting holes preserved.

**Reset from archive** (copies pristine car-1.5 exports into car-2):
```bash
cp exports/car-1.5/enclosure_body.{FCStd,step,stl} exports/car-2/
cp exports/car-1.5/enclosure_lid.{FCStd,step,stl} exports/car-2/
cp exports/car-1.5/telem_enclosure_assembly.FCStd exports/car-2/
```

**Regenerate preview GIF:**
```bash
tools/render-venv/bin/python cad/render_gif.py car-2
```

## `car-1.5/` — recovered SolidWorks archive (read-only baseline)

| File | Description |
|------|-------------|
| `SoftwareEnclosureBottomCar1.5.STEP` | Original SolidWorks body (source) |
| `SoftwareEnclosureTopCar1.5.STEP` | Original SolidWorks lid (source) |
| `enclosure_body.{FCStd,step,stl}` | Body aligned to origin via `cad/import_legacy.py` |
| `enclosure_lid.{FCStd,step,stl}` | Lid (already origin-aligned) |
| `telem_enclosure_assembly.FCStd` | Body + lid preview |

**Extents:** 228.6 × 223.5 × 57.2 mm (body + lid)

Regenerate from source STEP:
```bash
echo 'exec(open("cad/import_legacy.py").read())' | ./tools/squashfs-root/usr/bin/freecadcmd
```

## Experimental compact parametric model

`cad/enclosure.py` builds a separate 116 × 86 mm enclosure into `exports/car-2/` if run
directly — that workflow is **not** the current car-2 redesign. Do not run it unless you
intend to replace the legacy-based exports.
