import FreeCAD as App
import Part

shape = Part.read("exports/car-2/enclosure_body.step")

print("=== Holes on top face (Z ~ 50.8) ===")
for f in shape.Faces:
    try:
        surf = f.Surface
        if hasattr(surf, 'Radius') and abs(surf.Axis.z) > 0.9:
            c = f.CenterOfMass
            if c.z > 40:
                print(f"Hole: r={surf.Radius:.2f}, Center=({c.x:.2f}, {c.y:.2f}, {c.z:.2f})")
    except: pass
