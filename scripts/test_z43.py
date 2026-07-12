import FreeCAD as App
import Part

body = Part.read("exports/car-1.5/enclosure_body.step")

for f in body.Faces:
    bb = f.BoundBox
    if bb.ZMin < 43.0 and bb.ZMax > 43.0:
        # Just to check if it's not a vertical wall
        if abs(bb.XMax - bb.XMin) > 1e-2 and abs(bb.YMax - bb.YMin) > 1e-2:
            print(f"Non-vertical face crossing Z=43: X=[{bb.XMin:.1f}, {bb.XMax:.1f}], Y=[{bb.YMin:.1f}, {bb.YMax:.1f}], Z=[{bb.ZMin:.1f}, {bb.ZMax:.1f}]")
