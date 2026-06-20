"""Inspect Face 2 (X=228.6, normal +X) - the right short wall.
Find the rectangular cutout and all cylindrical holes on it.
"""
import FreeCAD as App
import Part

shape = Part.read("exports/car-2/enclosure_body.step")
bb = shape.BoundBox
print(f"BBox: X=[{bb.XMin:.3f}, {bb.XMax:.3f}], Y=[{bb.YMin:.3f}, {bb.YMax:.3f}], Z=[{bb.ZMin:.3f}, {bb.ZMax:.3f}]")

WALL_X = 228.6

print("\n--- Cylindrical holes on right wall (X~228.6, axis along X) ---")
for i, f in enumerate(shape.Faces):
    try:
        surf = f.Surface
        if hasattr(surf, 'Radius') and hasattr(surf, 'Axis'):
            ax = surf.Axis
            c = f.CenterOfMass
            r = surf.Radius
            if abs(ax.x) > 0.9 and abs(c.x - WALL_X) < 20 and r < 30:
                print(f"  Face {i}: r={r:.3f} (dia={2*r:.3f}), Center=({c.x:.3f}, {c.y:.3f}, {c.z:.3f})")
    except:
        pass

print("\n--- Flat faces with normal along X near X=228.6 ---")
for i, f in enumerate(shape.Faces):
    try:
        n = f.normalAt(0.5, 0.5)
        c = f.CenterOfMass
        if abs(n.x) > 0.95 and abs(c.x - WALL_X) < 20:
            bb2 = f.BoundBox
            print(f"  Face {i}: Area={f.Area:.2f}, Normal=({n.x:.2f},{n.y:.2f},{n.z:.2f}), "
                  f"Center=({c.x:.3f}, {c.y:.3f}, {c.z:.3f}), "
                  f"Y=[{bb2.YMin:.2f},{bb2.YMax:.2f}], Z=[{bb2.ZMin:.2f},{bb2.ZMax:.2f}]")
    except:
        pass
