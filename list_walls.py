import FreeCAD as App
import Part

shape = Part.read("exports/car-1.5/enclosure_body.step")

print("Vertical walls facing the interior (Z=7.6 floor):")
for i, f in enumerate(shape.Faces):
    try:
        area = f.Area
        if area > 1000:
            n = f.normalAt(0.5, 0.5) if hasattr(f, 'normalAt') else None
            if n and abs(n.z) < 0.1: # vertical
                bb = f.BoundBox
                # check if it touches the floor Z=7.6
                if abs(bb.ZMin - 7.6) < 0.5:
                    c = f.CenterOfMass
                    print(f"Wall at Center=({c.x:.1f}, {c.y:.1f}), Normal={n}, Area={area:.0f}")
    except:
        pass

