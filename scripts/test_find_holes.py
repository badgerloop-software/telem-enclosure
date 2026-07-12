import FreeCAD as App
import Part

body = Part.read("exports/car-1.5/enclosure_body.step")

left_holes = []
right_holes = []

for f in body.Faces:
    try:
        surf = f.Surface
        if hasattr(surf, 'Radius') and hasattr(surf, 'Axis'):
            ax = surf.Axis
            c = f.CenterOfMass
            r = surf.Radius
            if abs(ax.x) > 0.9 and r < 5.0: # small holes (dia < 10mm)
                if c.x < 15:
                    left_holes.append((c.y, c.z, r))
                elif c.x > 210:
                    right_holes.append((c.y, c.z, r))
    except:
        pass

def unique_holes(holes):
    unique = []
    for h in holes:
        if not any(abs(h[0]-u[0]) < 0.1 and abs(h[1]-u[1]) < 0.1 for u in unique):
            unique.append(h)
    return unique

print("Left holes:")
for h in unique_holes(left_holes):
    print(f"  Y={h[0]:.2f}, Z={h[1]:.2f}, R={h[2]:.2f}")

print("Right holes:")
for h in unique_holes(right_holes):
    print(f"  Y={h[0]:.2f}, Z={h[1]:.2f}, R={h[2]:.2f}")
