import FreeCAD as App
import Part

body = Part.read("exports/car-1.5/enclosure_body.step")

boss_box = Part.makeBox(6.0, 85.0, 40.0, App.Vector(134.6 - 0.2, 95.0, 8.0))
bosses = body.common(boss_box)
bosses.translate(App.Vector(-134.62, -136.17, 0))
bosses.rotate(App.Vector(0,0,0), App.Vector(0,0,1), -90)

bb = bosses.BoundBox
print(f"Bosses X min: {bb.XMin}, X max: {bb.XMax}")
print(f"Bosses width in X: {bb.XLength}")
