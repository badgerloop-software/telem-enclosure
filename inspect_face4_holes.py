"""Find all cylindrical holes on the X=0 (left short wall) face of the car-2 body."""
import FreeCAD as App
import Part

shape = Part.read("exports/car-2/enclosure_body.step")
bb = shape.BoundBox
print(f"BBox: X=[{bb.XMin:.3f}, {bb.XMax:.3f}], Y=[{bb.YMin:.3f}, {bb.YMax:.3f}], Z=[{bb.ZMin:.3f}, {bb.ZMax:.3f}]")

# The X=0 wall has outward normal pointing in -X direction.
# We want cylindrical faces (holes) whose axis is along X and whose center X is near 0.
print("\nAll cylindrical/conical surfaces near X=0 wall:")
for i, f in enumerate(shape.Faces):
    try:
        surf = f.Surface
        # Check for cylindrical surface
        if hasattr(surf, 'Radius') and hasattr(surf, 'Axis'):
            ax = surf.Axis
            c = f.CenterOfMass
            r = surf.Radius
            # We want holes on the X=0 face: axis roughly along X, center near X=0
            if abs(ax.x) > 0.9 and c.x < 15 and r < 30:
                print(f"  Face {i}: r={r:.3f} (dia={2*r:.3f}), Center=({c.x:.3f}, {c.y:.3f}, {c.z:.3f}), Axis=({ax.x:.2f},{ax.y:.2f},{ax.z:.2f})")
    except:
        pass

print("\nAll flat faces with normal in -X or +X direction near X=0:")
for i, f in enumerate(shape.Faces):
    try:
        n = f.normalAt(0.5, 0.5)
        c = f.CenterOfMass
        if abs(n.x) > 0.95 and c.x < 15:
            print(f"  Face {i}: Area={f.Area:.2f}, Center=({c.x:.3f}, {c.y:.3f}, {c.z:.3f}), Normal=({n.x:.2f},{n.y:.2f},{n.z:.2f})")
    except:
        pass
