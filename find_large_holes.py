import FreeCAD as App
import Part

shape = Part.read("exports/car-2/enclosure_body.step")

print("=== Large holes (radius > 4.5) ===")
for f in shape.Faces:
    try:
        surf = f.Surface
        if hasattr(surf, 'Radius') and surf.Radius > 4.5:
            c = f.CenterOfMass
            ax = surf.Axis
            print(f"Hole: r={surf.Radius:.2f}, Center=({c.x:.2f}, {c.y:.2f}, {c.z:.2f}), Axis=({ax.x:.2f}, {ax.y:.2f}, {ax.z:.2f})")
    except: pass
