import FreeCAD as App
import Part

doc = App.newDocument("Blueprints")
shape = Part.read("exports/car-2/enclosure_body.step")
obj = doc.addObject("Part::Feature", "Enclosure")
obj.Shape = shape

page = doc.addObject("TechDraw::DrawPage", "Page")
view_top = doc.addObject("TechDraw::DrawViewPart", "ViewTop")
view_top.Source = [obj]
view_top.Direction = (0, 0, 1)
view_top.X = 150
view_top.Y = 100
view_top.Scale = 0.5
page.addView(view_top)

doc.recompute()
try:
    page.exportPage("exports/car-2/blueprints.svg")
    print("Wrote exports/car-2/blueprints.svg")
except Exception as e:
    print(f"Failed to export: {e}")
