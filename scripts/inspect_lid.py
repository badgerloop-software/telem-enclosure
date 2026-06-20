import FreeCAD as App
import Part

shape = Part.read("exports/car-1.5/enclosure_lid.step")
bb = shape.BoundBox

print(f"Lid BBox: X=[{bb.XMin:.3f}, {bb.XMax:.3f}], Y=[{bb.YMin:.3f}, {bb.YMax:.3f}], Z=[{bb.ZMin:.3f}, {bb.ZMax:.3f}]")

print("=== Faces ===")
for i, f in enumerate(shape.Faces):
    try:
        bb2 = f.BoundBox
        if f.Area > 1000:
            print(f"Large Face {i}: Area={f.Area:.1f}, Z=[{bb2.ZMin:.1f},{bb2.ZMax:.1f}], X=[{bb2.XMin:.1f},{bb2.XMax:.1f}], Y=[{bb2.YMin:.1f},{bb2.YMax:.1f}]")
    except: pass

print("=== Holes ===")
for i, f in enumerate(shape.Faces):
    try:
        surf = f.Surface
        if hasattr(surf, 'Radius') and abs(surf.Axis.z) > 0.9:
            c = f.CenterOfMass
            print(f"Hole Face {i}: r={surf.Radius:.3f}, Center=({c.x:.3f},{c.y:.3f},{c.z:.3f})")
    except: pass
