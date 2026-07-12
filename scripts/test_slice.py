import FreeCAD as App
import Part

body = Part.read("exports/car-1.5/enclosure_body.step")

cut_box_top = Part.makeBox(500, 500, 100, App.Vector(-100, -100, 40.0))
bottom_half = body.cut(cut_box_top)
top_half = body.common(cut_box_top)

z40_faces = []
for f in bottom_half.Faces:
    bb = f.BoundBox
    if abs(bb.ZMin - 40.0) < 1e-3 and abs(bb.ZMax - 40.0) < 1e-3:
        z40_faces.append(f)

print(f"Found {len(z40_faces)} faces at Z=40")
if z40_faces:
    middle_section = z40_faces[0].extrude(App.Vector(0,0,10.0))
    for f in z40_faces[1:]:
        middle_section = middle_section.fuse(f.extrude(App.Vector(0,0,10.0)))

    top_half.translate(App.Vector(0, 0, 10.0))

    new_body = bottom_half.fuse(middle_section).fuse(top_half)
    new_body = new_body.removeSplitter()
    print(f"New body volume: {new_body.Volume:.0f}")
