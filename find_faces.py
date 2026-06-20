import FreeCAD as App
import Part

shape = Part.read("exports/car-1.5/enclosure_body.step")

print("Faces sorted by area (largest 20):")
faces = []
for i, f in enumerate(shape.Faces):
    try:
        area = f.Area
        c = f.CenterOfMass
        n = f.normalAt(0.5, 0.5) if hasattr(f, 'normalAt') else None
        faces.append((area, i, c, n, f.BoundBox))
    except:
        pass

faces.sort(reverse=True, key=lambda x: x[0])

for area, i, c, n, bb in faces[:20]:
    print(f"Index {i}: Area={area:.1f}, Center=({c.x:.1f}, {c.y:.1f}, {c.z:.1f}), Normal={n}, X=[{bb.XMin:.1f}, {bb.XMax:.1f}], Y=[{bb.YMin:.1f}, {bb.YMax:.1f}], Z=[{bb.ZMin:.1f}, {bb.ZMax:.1f}]")

