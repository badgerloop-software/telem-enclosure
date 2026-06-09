# Exports by car version

All generated model files are grouped by vehicle generation.

## `car-1.5/` — recovered SolidWorks design

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

## `car-2/` — parametric FreeCAD redesign

| File | Description |
|------|-------------|
| `enclosure_body.{FCStd,step,stl}` | Compact body built by `cad/enclosure.py` |
| `enclosure_lid.{FCStd,step,stl}` | Compact lid |
| `telem_enclosure_assembly.FCStd` | Assembly with reference component bricks |
| `enclosure_preview.gif` | Turntable animation |
| `face_templates.pdf` | 1:1 print-fit check sheets |

**Extents:** 116 × 86 × 60.5 mm (body + lid)

Regenerate parametric model:
```bash
echo 'exec(open("cad/enclosure.py").read())' | ./tools/squashfs-root/usr/bin/freecadcmd
```

Regenerate visuals:
```bash
tools/render-venv/bin/python cad/render_gif.py car-2
tools/render-venv/bin/python cad/face_templates.py
```
