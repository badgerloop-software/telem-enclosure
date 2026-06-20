import FreeCAD as App
import Part
import TechDraw

doc = App.newDocument("Blueprints")
shape = Part.read("exports/car-2/enclosure_body.step")
obj = doc.addObject("Part::Feature", "Enclosure")
obj.Shape = shape

page = doc.addObject("TechDraw::DrawPage", "Page")
template = doc.addObject("TechDraw::DrawSVGTemplate", "Template")
# Use a built-in blank A4 template if possible
import os
template.Template = os.path.join(App.getResourceDir(), "Mod", "TechDraw", "Templates", "A4_Landscape_blank.svg")
page.Template = template

view_top = doc.addObject("TechDraw::DrawViewPart", "ViewTop")
view_top.Source = [obj]
view_top.Direction = (0, 0, 1)
view_top.X = 150
view_top.Y = 100
view_top.Scale = 0.5
page.addView(view_top)

view_front = doc.addObject("TechDraw::DrawViewPart", "ViewFront")
view_front.Source = [obj]
view_front.Direction = (0, -1, 0)
view_front.X = 150
view_front.Y = 200
view_front.Scale = 0.5
page.addView(view_front)

doc.recompute()
page.exportPage("exports/car-2/blueprints.svg")
print("Wrote exports/car-2/blueprints.svg")
