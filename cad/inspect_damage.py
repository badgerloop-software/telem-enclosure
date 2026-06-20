"""Inspect floor features and L-step wall damage in car-2 vs car-1.5."""
from pathlib import Path
import sys
import FreeCAD as App
import Part

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

def inspect(label, path):
    print(f"\n{'='*70}")
    print(f"{label}: {path.name}")
    print(f"{'='*70}")
    shape = Part.read(str(path))
    bb = shape.BoundBox
    print(f"BBox: X[{bb.XMin:.2f}..{bb.XMax:.2f}] Y[{bb.YMin:.2f}..{bb.YMax:.2f}] Z[{bb.ZMin:.2f}..{bb.ZMax:.2f}]")

    # Cross-section at Z=5 (inside the floor slab) to find floor features
    print(f"\nCross-section at Z=5 (floor level):")
    try:
        plane = Part.makePlane(300, 300, App.Vector(-50, -50, 5), App.Vector(0, 0, 1))
        section = shape.section(plane)
        edges = sorted(section.Edges, key=lambda e: (round(e.Vertexes[0].Point.x,1), round(e.Vertexes[0].Point.y,1)))
        for i, e in enumerate(edges):
            v1, v2 = e.Vertexes[0].Point, e.Vertexes[-1].Point
            print(f"  edge#{i}: ({v1.x:.1f},{v1.y:.1f}) -> ({v2.x:.1f},{v2.y:.1f}) len={e.Length:.1f}")
    except Exception as ex:
        print(f"  Failed: {ex}")

    # Cross-section at Z=10 (just above floor) to find protruding floor features
    print(f"\nCross-section at Z=10 (just above floor):")
    try:
        plane = Part.makePlane(300, 300, App.Vector(-50, -50, 10), App.Vector(0, 0, 1))
        section = shape.section(plane)
        edges = sorted(section.Edges, key=lambda e: (round(e.Vertexes[0].Point.x,1), round(e.Vertexes[0].Point.y,1)))
        for i, e in enumerate(edges):
            v1, v2 = e.Vertexes[0].Point, e.Vertexes[-1].Point
            print(f"  edge#{i}: ({v1.x:.1f},{v1.y:.1f}) -> ({v2.x:.1f},{v2.y:.1f}) len={e.Length:.1f}")
    except Exception as ex:
        print(f"  Failed: {ex}")

    # Cross-section at X=130 (near L-step wall) to see wall damage
    print(f"\nCross-section at X=130 (near L-step wall):")
    try:
        plane = Part.makePlane(300, 300, App.Vector(130, -50, -50), App.Vector(1, 0, 0))
        section = shape.section(plane)
        edges = sorted(section.Edges, key=lambda e: (round(e.Vertexes[0].Point.y,1), round(e.Vertexes[0].Point.z,1)))
        for i, e in enumerate(edges):
            v1, v2 = e.Vertexes[0].Point, e.Vertexes[-1].Point
            print(f"  edge#{i}: ({v1.y:.1f},{v1.z:.1f}) -> ({v2.y:.1f},{v2.z:.1f}) len={e.Length:.1f}")
    except Exception as ex:
        print(f"  Failed: {ex}")

    # Find all planar faces near X=134.6 (L-step wall region)
    print(f"\nFaces near X=122..143 (L-step wall region):")
    for i, f in enumerate(shape.Faces):
        try:
            if f.Surface.__class__.__name__ != 'Plane':
                continue
            c = f.CenterOfMass
            bb_f = f.BoundBox
            if 120 < c.x < 145 or (120 < bb_f.XMin < 145 and bb_f.XLength < 20):
                n = f.Surface.Axis
                print(f"  face#{i} n=({n.x:.2f},{n.y:.2f},{n.z:.2f}) center=({c.x:.1f},{c.y:.1f},{c.z:.1f}) area={f.Area:.0f} bbox=X[{bb_f.XMin:.1f}..{bb_f.XMax:.1f}] Y[{bb_f.YMin:.1f}..{bb_f.YMax:.1f}] Z[{bb_f.ZMin:.1f}..{bb_f.ZMax:.1f}]")
        except:
            pass

    # Find floor features: horizontal faces at Z between 7 and 12 (above floor, below main cavity)
    print(f"\nHorizontal faces at Z=7..12 (floor-level protrusions):")
    for i, f in enumerate(shape.Faces):
        try:
            if f.Surface.__class__.__name__ != 'Plane':
                continue
            n = f.Surface.Axis
            if abs(n.z) < 0.9:
                continue
            c = f.CenterOfMass
            if 7 < c.z < 12 and f.Area > 20:
                bb_f = f.BoundBox
                print(f"  face#{i} n=({n.x:.2f},{n.y:.2f},{n.z:.2f}) center=({c.x:.1f},{c.y:.1f},{c.z:.1f}) area={f.Area:.0f} bbox=X[{bb_f.XMin:.1f}..{bb_f.XMax:.1f}] Y[{bb_f.YMin:.1f}..{bb_f.YMax:.1f}] Z[{bb_f.ZMin:.1f}..{bb_f.ZMax:.1f}]")
        except:
            pass

car15 = ROOT / "exports" / "car-1.5" / "enclosure_body.step"
car2 = ROOT / "exports" / "car-2" / "enclosure_body.step"

inspect("CAR 1.5 BASELINE", car15)
inspect("CAR 2 CURRENT", car2)
