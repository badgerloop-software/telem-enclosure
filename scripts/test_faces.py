import FreeCAD as App
import Part

shape = Part.read("exports/car-1.5/enclosure_body.step")
bb = shape.BoundBox
print(f"Bounding Box: X=[{bb.XMin:.2f}, {bb.XMax:.2f}], Y=[{bb.YMin:.2f}, {bb.YMax:.2f}], Z=[{bb.ZMin:.2f}, {bb.ZMax:.2f}]")

print("Faces with normal parallel to X axis:")
for i, f in enumerate(shape.Faces):
    try:
        n = f.normalAt(0.5, 0.5)
        if abs(n.x) > 0.99:
            c = f.CenterOfMass
            print(f"  Face {i}: Area={f.Area:.1f}, Center=({c.x:.2f}, {c.y:.2f}, {c.z:.2f}), Normal=({n.x:.1f}, {n.y:.1f}, {n.z:.1f})")
    except:
        pass
