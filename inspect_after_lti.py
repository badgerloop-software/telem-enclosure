"""Inspect current car-2 model after L→I cut to find what holes were lost."""
import FreeCAD as App
import Part

shape = Part.read("exports/car-2/enclosure_body.step")
bb = shape.BoundBox
print(f"BBox: X=[{bb.XMin:.3f},{bb.XMax:.3f}], Y=[{bb.YMin:.3f},{bb.YMax:.3f}], Z=[{bb.ZMin:.3f},{bb.ZMax:.3f}]")

print("\n=== Y-axis flat faces (inner back wall region) ===")
for i, f in enumerate(shape.Faces):
    try:
        n = f.normalAt(0.5, 0.5)
        c = f.CenterOfMass
        bb2 = f.BoundBox
        if abs(n.y) > 0.95 and 85 < bb2.YMin < 110 and f.Area > 5:
            print(f"  Face {i}: Area={f.Area:.2f}, N=({n.x:.2f},{n.y:.2f},{n.z:.2f}), "
                  f"Y={bb2.YMin:.4f}..{bb2.YMax:.4f}, "
                  f"X=[{bb2.XMin:.3f},{bb2.XMax:.3f}], Z=[{bb2.ZMin:.3f},{bb2.ZMax:.3f}]")
    except: pass

print("\n=== All cylindrical surfaces (holes/bosses) near the inner back wall region (Y=80-110) ===")
for i, f in enumerate(shape.Faces):
    try:
        surf = f.Surface
        if hasattr(surf, 'Radius') and hasattr(surf, 'Axis'):
            c = f.CenterOfMass
            r = surf.Radius
            if 80 < c.y < 115 and r < 10:
                ax = surf.Axis
                print(f"  Face {i}: r={r:.4f}, Center=({c.x:.3f},{c.y:.3f},{c.z:.3f}), Axis=({ax.x:.2f},{ax.y:.2f},{ax.z:.2f})")
    except: pass

print("\n=== All cylindrical surfaces on or near the original Y=220.98 area (now gone, confirm) ===")
print("  (should be empty if cut correctly)")
for i, f in enumerate(shape.Faces):
    try:
        surf = f.Surface
        if hasattr(surf, 'Radius') and hasattr(surf, 'Axis'):
            c = f.CenterOfMass
            if c.y > 105:
                print(f"  Face {i}: r={surf.Radius:.3f}, Center=({c.x:.3f},{c.y:.3f},{c.z:.3f})")
    except: pass

print("\n=== X-axis inner divider wall (X~134.62) faces ===")
for i, f in enumerate(shape.Faces):
    try:
        n = f.normalAt(0.5, 0.5)
        c = f.CenterOfMass
        bb2 = f.BoundBox
        if abs(n.x) > 0.95 and 130 < bb2.XMin < 140 and f.Area > 5:
            print(f"  Face {i}: Area={f.Area:.2f}, N=({n.x:.2f},{n.y:.2f},{n.z:.2f}), "
                  f"X={bb2.XMin:.3f}, Y=[{bb2.YMin:.3f},{bb2.YMax:.3f}], Z=[{bb2.ZMin:.3f},{bb2.ZMax:.3f}]")
    except: pass
