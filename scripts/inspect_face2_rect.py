"""Find the rectangular cutout on the right short wall by looking at the
interior recessed face and any non-cylindrical geometry near X=228.6.
"""
import FreeCAD as App
import Part

shape = Part.read("exports/car-2/enclosure_body.step")

WALL_X = 228.6

print("All faces near right wall (X=220-228.6) that are NOT the main flat faces or cylinders:")
for i, f in enumerate(shape.Faces):
    try:
        surf = f.Surface
        c = f.CenterOfMass
        bb2 = f.BoundBox
        # Skip cylindrical
        if hasattr(surf, 'Radius'):
            continue
        # Only near right wall
        if bb2.XMax < 218 or bb2.XMin > 229:
            continue
        n = f.normalAt(0.5, 0.5)
        # Skip the main outer face
        if f.Area > 5000:
            continue
        print(f"  Face {i}: Area={f.Area:.2f}, Center=({c.x:.2f},{c.y:.2f},{c.z:.2f}), "
              f"Normal=({n.x:.2f},{n.y:.2f},{n.z:.2f}), "
              f"X=[{bb2.XMin:.2f},{bb2.XMax:.2f}], Y=[{bb2.YMin:.2f},{bb2.YMax:.2f}], Z=[{bb2.ZMin:.2f},{bb2.ZMax:.2f}]")
    except:
        pass

# Also print a map of what hole positions exist vs. where we'd expect them
print("\n\nExisting hole positions on right wall (Y, Z):")
holes = set()
for i, f in enumerate(shape.Faces):
    try:
        surf = f.Surface
        if hasattr(surf, 'Radius') and hasattr(surf, 'Axis'):
            ax = surf.Axis
            c = f.CenterOfMass
            r = surf.Radius
            if abs(ax.x) > 0.9 and abs(c.x - 224.79) < 5 and abs(r - 2.54) < 0.1:
                holes.add((round(c.y, 1), round(c.z, 1)))
    except:
        pass

# Find the grid bounds
ys = sorted(set(y for y,z in holes))
zs = sorted(set(z for y,z in holes))
print(f"Y positions: {ys}")
print(f"Z positions: {zs}")

# Find all positions in grid that are MISSING (those are inside the cutout)
print("\nMissing grid positions (inside rectangular cutout):")
all_ys = [y for y in [10.16, 20.32, 30.48, 40.64, 50.80, 60.96, 71.12, 81.28, 91.44,
                       101.60, 111.76, 121.92, 132.08, 142.24, 152.40, 162.56, 172.72,
                       182.88, 193.04, 203.20, 213.36]]
all_zs = [z for z in [10.16, 20.32, 30.48, 40.64]]
missing = []
for y in all_ys:
    for z in all_zs:
        key = (round(y,1), round(z,1))
        if key not in holes:
            missing.append((y, z))
            print(f"  Y={y:.2f}, Z={z:.2f}")
