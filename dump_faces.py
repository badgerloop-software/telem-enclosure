import FreeCAD as App
import Part

for name, path in [("car-1.5", "exports/car-1.5/enclosure_body.step"), 
                   ("car-2", "exports/car-2/enclosure_body.step"),
                   ("car-2 FCStd", "exports/car-2/enclosure_body.FCStd")]:
    print(f"\n--- {name} ---")
    if "FCStd" in path:
        doc = App.openDocument(path)
        shape = doc.getObject("Body").Shape
    else:
        shape = Part.read(path)
    
    for idx in range(15):
        try:
            f = shape.Faces[idx]
            c = f.CenterOfMass
            n = f.normalAt(0.5, 0.5) if hasattr(f, 'normalAt') else None
            area = f.Area
            print(f"Face {idx+1}: Area={area:.1f}, Center=({c.x:.2f}, {c.y:.2f}, {c.z:.2f}) Normal={n}")
        except:
            pass
