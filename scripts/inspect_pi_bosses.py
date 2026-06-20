import FreeCAD as App
import Part

shape = Part.read("exports/car-1.5/enclosure_body.step")

print("=== Pi 4 Bosses in car-1.5 ===")
for i, f in enumerate(shape.Faces):
    try:
        surf = f.Surface
        if hasattr(surf, 'Radius') and abs(surf.Axis.z) > 0.9:
            c = f.CenterOfMass
            # The PI bosses were around X=163.6, Y=94.7, Z > 7.62
            if 160 < c.x < 170 and 90 < c.y < 100 and c.z > 7:
                print(f"Face {i}: r={surf.Radius:.3f}, Center=({c.x:.3f},{c.y:.3f},{c.z:.3f}), Z bounds=[{f.BoundBox.ZMin:.2f}, {f.BoundBox.ZMax:.2f}]")
    except: pass
