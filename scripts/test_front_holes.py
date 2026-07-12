import FreeCAD as App
import Part

body = Part.read("exports/car-2/enclosure_body.step")

print("Holes on front wall (Y < 10):")
for f in body.Faces:
    try:
        surf = f.Surface
        if hasattr(surf, 'Radius') and hasattr(surf, 'Axis'):
            ax = surf.Axis
            c = f.CenterOfMass
            r = surf.Radius
            if c.y < 10 and abs(ax.y) > 0.9:
                print(f"  Center=({c.x:.2f}, {c.y:.2f}, {c.z:.2f}), Dia={r*2:.3f}, Axis=({ax.x:.1f}, {ax.y:.1f}, {ax.z:.1f})")
    except:
        pass
