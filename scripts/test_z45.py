import FreeCAD as App
import Part

body = Part.read("exports/car-1.5/enclosure_body.step")

for z_test in [42.0, 43.5, 44.0, 45.0, 46.0, 47.0]:
    cross_faces = 0
    for f in body.Faces:
        bb = f.BoundBox
        if bb.ZMin < z_test and bb.ZMax > z_test:
            if abs(bb.XMax - bb.XMin) > 1e-2 and abs(bb.YMax - bb.YMin) > 1e-2:
                cross_faces += 1
    print(f"Z={z_test}: {cross_faces} non-vertical faces")
