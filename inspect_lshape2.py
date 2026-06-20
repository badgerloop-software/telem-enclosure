"""Full geometric map of the L-shape step wall and all related features."""
import FreeCAD as App
import Part

shape = Part.read("exports/car-2/enclosure_body.step")

print("=== ALL Y-axis walls (to map the L-shape precisely) ===")
for i, f in enumerate(shape.Faces):
    try:
        n = f.normalAt(0.5, 0.5)
        c = f.CenterOfMass
        bb2 = f.BoundBox
        if abs(n.y) > 0.95 and f.Area > 10:
            print(f"  Face {i}: Area={f.Area:.1f}, N=({n.x:.1f},{n.y:.1f},{n.z:.1f}), "
                  f"Y={bb2.YMin:.3f}..{bb2.YMax:.3f}, "
                  f"X={bb2.XMin:.3f}..{bb2.XMax:.3f}, "
                  f"Z={bb2.ZMin:.3f}..{bb2.ZMax:.3f}")
    except: pass

print("\n=== ALL X-axis walls (outer left/right walls) ===")
for i, f in enumerate(shape.Faces):
    try:
        n = f.normalAt(0.5, 0.5)
        c = f.CenterOfMass
        bb2 = f.BoundBox
        if abs(n.x) > 0.95 and f.Area > 100:
            print(f"  Face {i}: Area={f.Area:.1f}, N=({n.x:.1f},{n.y:.1f},{n.z:.1f}), "
                  f"X={bb2.XMin:.3f}..{bb2.XMax:.3f}, "
                  f"Y={bb2.YMin:.3f}..{bb2.YMax:.3f}, "
                  f"Z={bb2.ZMin:.3f}..{bb2.ZMax:.3f}")
    except: pass

print("\n=== Floor holes (Z-axis cylinders, axis along Z, near floor) ===")
for i, f in enumerate(shape.Faces):
    try:
        surf = f.Surface
        if hasattr(surf, 'Radius') and hasattr(surf, 'Axis'):
            ax = surf.Axis
            c = f.CenterOfMass
            r = surf.Radius
            if abs(ax.z) > 0.9 and c.z < 8 and r < 6 and r > 1:
                bb2 = f.BoundBox
                print(f"  Face {i}: r={r:.4f} (dia={2*r:.3f}), "
                      f"Center=({c.x:.3f},{c.y:.3f},{c.z:.3f}), "
                      f"Z={bb2.ZMin:.3f}..{bb2.ZMax:.3f}")
    except: pass
