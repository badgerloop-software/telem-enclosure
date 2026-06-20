import FreeCAD as App
import Part

shape = Part.read("exports/car-1.5/enclosure_body.step")

print("=== Cylindrical faces on the right arm inner/outer walls ===")
for i, f in enumerate(shape.Faces):
    try:
        surf = f.Surface
        if hasattr(surf, 'Radius') and hasattr(surf, 'Axis'):
            c = f.CenterOfMass
            # Right arm Y > 101.6, X > 127
            if c.x > 120 and c.y > 100:
                ax = surf.Axis
                print(f"  Face {i}: r={surf.Radius:.3f}, Center=({c.x:.3f},{c.y:.3f},{c.z:.3f}), Axis=({ax.x:.2f},{ax.y:.2f},{ax.z:.2f})")
    except: pass
