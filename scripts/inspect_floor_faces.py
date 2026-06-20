"""Inspect faces 2-8 area: all flat faces near Z=7.62 (the interior floor plane).
Face 2 is at Z=7.621 (normal +Z). Other faces must be depressions/steps slightly below.
Find them precisely so we can fill them flush.
"""
import FreeCAD as App
import Part

shape = Part.read("exports/car-2/enclosure_body.step")

# From selection: all faces near Z=7.22 to 7.62, normal roughly +Z
# The combined bbox Z=[7.221, 7.621], so faces 3-8 are slightly BELOW face 2's level.
TARGET_Z = 7.621  # Face 2 level

print("Flat faces with normal +Z near Z=7.6 (interior floor area):")
for i, f in enumerate(shape.Faces):
    try:
        n = f.normalAt(0.5, 0.5)
        c = f.CenterOfMass
        bb2 = f.BoundBox
        if abs(n.z) > 0.95 and n.z > 0 and bb2.ZMin > 5.0 and bb2.ZMax < 10.0:
            print(f"  Face {i}: Area={f.Area:.2f}, Center=({c.x:.3f},{c.y:.3f},{c.z:.3f}), "
                  f"Z=[{bb2.ZMin:.4f},{bb2.ZMax:.4f}], "
                  f"Y=[{bb2.YMin:.3f},{bb2.YMax:.3f}], X=[{bb2.XMin:.3f},{bb2.XMax:.3f}]")
    except:
        pass

print("\nFlat faces with normal -Z near Z=7.6 (bottom of depressions):")
for i, f in enumerate(shape.Faces):
    try:
        n = f.normalAt(0.5, 0.5)
        c = f.CenterOfMass
        bb2 = f.BoundBox
        if abs(n.z) > 0.95 and n.z < 0 and bb2.ZMax > 5.0 and bb2.ZMax < 10.0:
            print(f"  Face {i}: Area={f.Area:.2f}, Center=({c.x:.3f},{c.y:.3f},{c.z:.3f}), "
                  f"Z=[{bb2.ZMin:.4f},{bb2.ZMax:.4f}], "
                  f"Y=[{bb2.YMin:.3f},{bb2.YMax:.3f}], X=[{bb2.XMin:.3f},{bb2.XMax:.3f}]")
    except:
        pass
