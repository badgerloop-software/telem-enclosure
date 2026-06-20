"""Deep inspection of the L-shape / stepped wall region.
Find all faces near the Y-axis walls to understand the L-shape geometry.
"""
import FreeCAD as App
import Part

shape = Part.read("exports/car-2/enclosure_body.step")
bb = shape.BoundBox
print(f"BBox: X=[{bb.XMin:.3f}, {bb.XMax:.3f}], Y=[{bb.YMin:.3f}, {bb.YMax:.3f}], Z=[{bb.ZMin:.3f}, {bb.ZMax:.3f}]")

print("\n=== All flat faces with normal along Y axis ===")
for i, f in enumerate(shape.Faces):
    try:
        n = f.normalAt(0.5, 0.5)
        c = f.CenterOfMass
        bb2 = f.BoundBox
        if abs(n.y) > 0.95 and f.Area > 10:
            print(f"  Face {i}: Area={f.Area:.2f}, Normal=({n.x:.2f},{n.y:.2f},{n.z:.2f}), "
                  f"Center=({c.x:.3f},{c.y:.3f},{c.z:.3f}), "
                  f"X=[{bb2.XMin:.3f},{bb2.XMax:.3f}], Y=[{bb2.YMin:.3f},{bb2.YMax:.3f}], Z=[{bb2.ZMin:.3f},{bb2.ZMax:.3f}]")
    except:
        pass

print("\n=== All flat faces with normal along Z axis near bottom (Z < 15) ===")
for i, f in enumerate(shape.Faces):
    try:
        n = f.normalAt(0.5, 0.5)
        c = f.CenterOfMass
        bb2 = f.BoundBox
        if abs(n.z) > 0.95 and bb2.ZMax < 20 and f.Area > 50:
            print(f"  Face {i}: Area={f.Area:.2f}, Normal=({n.x:.2f},{n.y:.2f},{n.z:.2f}), "
                  f"Center=({c.x:.3f},{c.y:.3f},{c.z:.3f}), "
                  f"X=[{bb2.XMin:.3f},{bb2.XMax:.3f}], Y=[{bb2.YMin:.3f},{bb2.YMax:.3f}], Z=[{bb2.ZMin:.3f},{bb2.ZMax:.3f}]")
    except:
        pass

print("\n=== Cylindrical holes near the bottom floor (Z < 15, axis along Z) ===")
for i, f in enumerate(shape.Faces):
    try:
        surf = f.Surface
        if hasattr(surf, 'Radius') and hasattr(surf, 'Axis'):
            ax = surf.Axis
            c = f.CenterOfMass
            r = surf.Radius
            if abs(ax.z) > 0.9 and c.z < 15 and r < 15:
                print(f"  Face {i}: r={r:.3f} (dia={2*r:.3f}), Center=({c.x:.3f},{c.y:.3f},{c.z:.3f})")
    except:
        pass
