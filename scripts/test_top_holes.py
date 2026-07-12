import FreeCAD as App
import Part

body = Part.read("exports/car-1.5/enclosure_body.step")

print("Top face holes (Z ~ 50.8):")
for f in body.Faces:
    try:
        surf = f.Surface
        if hasattr(surf, 'Radius') and hasattr(surf, 'Axis'):
            ax = surf.Axis
            c = f.CenterOfMass
            r = surf.Radius
            bb = f.BoundBox
            if abs(ax.z) > 0.9 and bb.ZMax > 50:
                print(f"  Center=({c.x:.2f}, {c.y:.2f}, {c.z:.2f}), R={r:.3f}, ZMax={bb.ZMax:.2f}")
    except:
        pass
