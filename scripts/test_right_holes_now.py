import FreeCAD as App
import Part

body = Part.read("exports/car-2/enclosure_body.step")

print("Holes on right wall (X > 220):")
for f in body.Faces:
    try:
        surf = f.Surface
        if hasattr(surf, 'Radius') and hasattr(surf, 'Axis'):
            ax = surf.Axis
            c = f.CenterOfMass
            r = surf.Radius
            if c.x > 220:
                print(f"  Center=({c.x:.2f}, {c.y:.2f}, {c.z:.2f}), Dia={r*2:.3f}, Axis=({ax.x:.1f}, {ax.y:.1f}, {ax.z:.1f})")
    except:
        pass
