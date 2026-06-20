import FreeCAD as App
import Part

shape = Part.read("exports/car-2/enclosure_body.step")

print("Checking X=175 to 195, Y=40 to 105, Z=7 to 45")
faces_found = 0
for f in shape.Faces:
    bb = f.BoundBox
    # check intersection with our bounding box
    if not (bb.XMax < 175 or bb.XMin > 195 or bb.YMax < 40 or bb.YMin > 105 or bb.ZMax < 7 or bb.ZMin > 45):
        # Could be an intersecting face
        faces_found += 1
        c = f.CenterOfMass
        print(f"Face inside: Area={f.Area:.1f}, Center=({c.x:.1f},{c.y:.1f},{c.z:.1f}), X=[{bb.XMin:.1f},{bb.XMax:.1f}], Y=[{bb.YMin:.1f},{bb.YMax:.1f}]")
