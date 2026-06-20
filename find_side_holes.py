import FreeCAD as App
import Part

shape = Part.read("exports/car-2/enclosure_body.step")

print("=== Left wall (X around 0) holes ===")
for f in shape.Faces:
    try:
        if hasattr(f.Surface, 'Radius') and f.Surface.Axis.x > 0.9:
            c = f.CenterOfMass
            if c.x < 15:
                print(f"Hole: r={f.Surface.Radius:.2f}, Center=({c.x:.2f}, {c.y:.2f}, {c.z:.2f})")
    except: pass

print("\n=== Right wall (X around 228) holes ===")
for f in shape.Faces:
    try:
        if hasattr(f.Surface, 'Radius') and f.Surface.Axis.x > 0.9:
            c = f.CenterOfMass
            if c.x > 215:
                print(f"Hole: r={f.Surface.Radius:.2f}, Center=({c.x:.2f}, {c.y:.2f}, {c.z:.2f})")
    except: pass
