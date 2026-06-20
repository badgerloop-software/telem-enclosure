import FreeCAD as App
import Part

shape = Part.read("exports/car-1.5/enclosure_body.step")

holes = []
for f in shape.Faces:
    try:
        r = f.Surface.Radius
        if r > 0 and r < 15:
            holes.append((round(r, 3), f.CenterOfMass))
    except:
        pass

groups = {}
for r, c in holes:
    groups.setdefault(r, []).append(c)

print("Hole groups with exactly 8 faces (usually 4 cylindrical holes):")
for r, centers in groups.items():
    if len(centers) == 8:
        print(f"\nRadius {r} (Dia {2*r}):")
        for c in centers:
            print(f"  {c.x:.2f}, {c.y:.2f}, {c.z:.2f}")

print("\nHole groups with exactly 4 faces (maybe 4 cylindrical holes with 1 face each?):")
for r, centers in groups.items():
    if len(centers) == 4:
        print(f"\nRadius {r} (Dia {2*r}):")
        for c in centers:
            print(f"  {c.x:.2f}, {c.y:.2f}, {c.z:.2f}")

print("\nHole groups with exactly 16 faces (maybe 4 holes with 4 faces each?):")
for r, centers in groups.items():
    if len(centers) == 16:
        print(f"\nRadius {r} (Dia {2*r}):")
        for c in centers:
            print(f"  {c.x:.2f}, {c.y:.2f}, {c.z:.2f}")
