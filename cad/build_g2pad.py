"""Build the G2Pad FreeCAD model (g2pad.FCStd) and export STEP files.

Run with FreeCAD 1.0+ from the repo root:
    freecadcmd cad/build_g2pad.py
Everything is parametric through the constants below. Units: mm, Z up.
The board centre is the XY origin; the USB-C end of the pad faces -Y.
"""
import os
import FreeCAD as App
import Part
import Import
from FreeCAD import Vector as V

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else os.path.join(os.getcwd(), "cad")
OUT = HERE

# ---------------------------------------------------------------- parameters
PCB_W, PCB_H, PCB_T = 42.0, 64.0, 1.6
GAP = 0.5            # PCB to wall clearance
WALL = 2.0
FLOOR = 1.6
R_OUT = 3.5          # outer corner radius
PCB_Z = 9.5          # PCB bottom (leaves room for the LiPo under the board)
PCB_TOP = PCB_Z + PCB_T
PLATE_T = 1.5
PLATE_TOP = PCB_TOP + 5.0   # MX standard: plate top 5 mm above PCB top
PLATE_Z = PLATE_TOP - PLATE_T
PITCH = 19.05
KEYS = {  # name: (x, y) key centres, board coordinates
    "Back_Q": (-PITCH / 2, 20.5),
    "Up_W": (PITCH / 2, 20.5),
    "Select_E": (-PITCH / 2, 20.5 - PITCH),
    "Down_S": (PITCH / 2, 20.5 - PITCH),
}
HOLES = [(-18.4, 29.4), (18.4, 29.4), (17.5, -28.5)]   # M2, matches the PCB
XIAO = (0.0, -20.5)          # XIAO centre; USB-C at -Y edge
SWITCH_PWR = (-18.1, -26.0)  # PCM12 slide switch, lever out the -X wall
BATTERY = (0.0, 6.0, 20.0, 30.0, 4.0)  # x, y, w, l, t (402030 LiPo)

OUT_W = PCB_W + 2 * (GAP + WALL)
OUT_H = PCB_H + 2 * (GAP + WALL)


def rbox(w, h, t, r, x=0, y=0, z=0):
    """Box centred on (x, y) with rounded vertical edges."""
    b = Part.makeBox(w, h, t, V(x - w / 2, y - h / 2, z))
    if r > 0:
        edges = [e for e in b.Edges if abs(e.Vertexes[0].Point.z - e.Vertexes[1].Point.z) > 1e-6]
        b = b.makeFillet(r, edges)
    return b


def rrect(w, h, r, x=0, y=0, z=0):
    """Closed rounded-rectangle wire in the XY plane at height z."""
    import math
    hw, hh = w / 2, h / 2
    e = []
    corners = [(hw - r, hh - r, 0), (-hw + r, hh - r, 90), (-hw + r, -hh + r, 180), (hw - r, -hh + r, 270)]
    pts = []
    for (cx, cy, a0) in corners:
        a = math.radians(a0)
        a1 = math.radians(a0 + 90)
        am = math.radians(a0 + 45)
        p0 = V(x + cx + r * math.cos(a), y + cy + r * math.sin(a), z)
        pm = V(x + cx + r * math.cos(am), y + cy + r * math.sin(am), z)
        p1 = V(x + cx + r * math.cos(a1), y + cy + r * math.sin(a1), z)
        pts.append((p0, pm, p1))
    for i, (p0, pm, p1) in enumerate(pts):
        e.append(Part.Arc(p0, pm, p1).toShape())
        nxt = pts[(i + 1) % 4][0]
        e.append(Part.LineSegment(p1, nxt).toShape())
    return Part.Wire(e)


def cyl(r, h, x, y, z):
    return Part.makeCylinder(r, h, V(x, y, z))


# ---------------------------------------------------------------- printed parts
def make_tray():
    wall_top = PLATE_Z
    t = rbox(OUT_W, OUT_H, wall_top, R_OUT)
    t = t.cut(rbox(OUT_W - 2 * WALL, OUT_H - 2 * WALL, wall_top, R_OUT - WALL, z=FLOOR))
    # standoffs with clearance holes; screws come up from below into the plate bosses
    for (x, y) in HOLES:
        t = t.fuse(cyl(2.4, PCB_Z - FLOOR, x, y, FLOOR))
    for (x, y) in HOLES:
        t = t.cut(cyl(1.15, PCB_Z + 1, x, y, -0.5))
        t = t.cut(cyl(2.1, 1.4, x, y, -0.01))   # counterbore for M2 head
    # battery locating ribs
    bx, by, bw, bl, bt = BATTERY
    for sx in (-1, 1):
        t = t.fuse(Part.makeBox(1.2, bl * 0.6, 2.0, V(bx + sx * (bw / 2 + 1.0) - 0.6, by - bl * 0.3, FLOOR)))
    # USB-C opening (-Y wall)
    t = t.cut(Part.makeBox(12.0, WALL + 2, wall_top, V(XIAO[0] - 6.0, -OUT_H / 2 - 1, PCB_TOP - 0.6)))
    # power switch slot (-X wall)
    t = t.cut(Part.makeBox(WALL + 2, 6.0, 3.0, V(-OUT_W / 2 - 1, SWITCH_PWR[1] - 3.0, PCB_TOP - 0.3)))
    # lanyard hole through the +Y corner
    t = t.cut(Part.makeCylinder(1.2, 8, V(OUT_W / 2 - 5, OUT_H / 2 + 1, 4.5), V(0, -1, 0)))
    return t


def make_plate():
    p = rbox(OUT_W, OUT_H, PLATE_T, R_OUT, z=PLATE_Z)
    for (x, y) in KEYS.values():
        p = p.cut(Part.makeBox(14.0, 14.0, 10, V(x - 7.0, y - 7.0, PLATE_Z - 1)))
    # screw bosses down to the PCB top
    for (x, y) in HOLES:
        p = p.fuse(cyl(2.0, PLATE_Z - PCB_TOP, x, y, PCB_TOP))
        p = p.cut(cyl(0.8, PLATE_Z - PCB_TOP + 1.0, x, y, PCB_TOP - 0.01))  # M2 self-tap pilot
    # clearance pocket over the XIAO (USB-C shell is ~3.2 mm tall)
    p = p.cut(rbox(19.0, 22.5, 0.8, 1.0, XIAO[0], XIAO[1] - 0.5, PLATE_Z - 0.01))
    # shallow recess for a name badge between the keys and the USB end
    p = p.cut(rbox(22.0, 6.0, 0.4, 1.0, 0, -22.0, PLATE_TOP - 0.4))
    return p


# ---------------------------------------------------------------- bought parts (simplified models)
def make_switch(x, y):
    s = rbox(14.0, 14.0, 5.0, 0.5, x, y, PCB_TOP)              # bottom housing (below plate)
    s = s.fuse(rbox(15.6, 15.6, 0.0 + 0.8, 0.5, x, y, PLATE_TOP))  # flange on the plate
    s = s.fuse(Part.makeLoft([rrect(15.0, 15.0, 0.5, x, y, PLATE_TOP + 0.8),
                              rrect(10.5, 10.0, 0.5, x, y, PCB_TOP + 11.6)], True))
    s = s.fuse(Part.makeBox(4.0, 1.3, 3.6, V(x - 2.0, y - 0.65, PCB_TOP + 11.6)))   # stem +
    s = s.fuse(Part.makeBox(1.3, 4.0, 3.6, V(x - 0.65, y - 2.0, PCB_TOP + 11.6)))
    for (dx, dy) in ((2.54, 5.08), (-3.81, 2.54)):   # pins
        s = s.fuse(cyl(0.75, 3.3, x + dx, y + dy, PCB_Z - 3.3 + PCB_T))
    return s


def make_keycap(x, y):
    z0 = PCB_TOP + 11.6 + 0.6
    top_z = z0 + 8.0
    base = rrect(18.0, 18.0, 1.0, x, y, z0)
    top = rrect(12.5, 14.0, 2.0, x, y + 0.8, top_z)
    cap = Part.makeLoft([base, top], True)
    cap = cap.cut(Part.makeLoft([rrect(16.4, 16.4, 0.8, x, y, z0 - 0.01),
                                 rrect(11.0, 12.4, 1.5, x, y + 0.8, top_z - 1.4)], True))
    cap = cap.fuse(cyl(2.8, top_z - z0 - 1.4 - 0.5, x, y, z0 + 0.5))  # stem socket
    cap = cap.cut(Part.makeBox(4.1, 1.35, 4.5, V(x - 2.05, y - 0.675, z0 - 0.1)))
    cap = cap.cut(Part.makeBox(1.35, 4.1, 4.5, V(x - 0.675, y - 2.05, z0 - 0.1)))
    # gentle cylindrical dish
    cap = cap.cut(Part.makeCylinder(30.0, 30, V(x - 15, y + 0.8, top_z + 30 - 0.8), V(1, 0, 0)))
    return cap


def make_xiao():
    x, y = XIAO
    b = rbox(17.8, 21.0, 1.0, 0.8, x, y, PCB_TOP)
    b = b.fuse(rbox(12.5, 10.5, 1.6, 0.3, x, y + 3.0, PCB_TOP + 1.0))           # RF shield can
    b = b.fuse(rbox(8.94, 7.35, 3.16, 1.2, x, y - 21.0 / 2 + 3.4, PCB_TOP + 1.0))  # USB-C receptacle
    return b


def make_battery():
    bx, by, bw, bl, bt = BATTERY
    return rbox(bw, bl, bt, 1.0, bx, by, FLOOR + 0.2)


def make_pwr_switch():
    x, y = SWITCH_PWR
    s = Part.makeBox(3.5, 6.7, 1.4, V(x - 1.0, y - 3.35, PCB_TOP))
    s = s.fuse(Part.makeBox(2.0, 1.3, 1.0, V(x - 3.0, y - 0.65, PCB_TOP + 0.2)))
    return s


def make_jst():
    # JST-PH socket is mounted on the BACK of the PCB, next to the LiPo
    return Part.makeBox(4.5, 6.0, 6.0, V(-12.0 - 2.25 - 0.4, -23.6 - 3.0 + 0.6, PCB_Z - 6.0))


# ---------------------------------------------------------------- document
doc = App.newDocument("g2pad")
enclosure = doc.addObject("App::Part", "Enclosure")
electronics = doc.addObject("App::Part", "Electronics")
keycaps = doc.addObject("App::Part", "Keycaps")


def add(container, name, shape, color=None):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    container.addObject(o)
    return o


tray = add(enclosure, "BottomTray", make_tray())
plate = add(enclosure, "TopPlate", make_plate())

pcb = Part.read(os.path.join(HERE, "step", "g2pad_pcb.step"))
pcb.translate(V(-121.0, 132.0, PCB_Z))
add(electronics, "PCB", pcb)
add(electronics, "XIAO_nRF52840", make_xiao())
add(electronics, "LiPo_402030", make_battery())
add(electronics, "PowerSwitch_PCM12", make_pwr_switch())
add(electronics, "JST_PH_Battery", make_jst())
for n, (x, y) in KEYS.items():
    add(electronics, "Switch_" + n, make_switch(x, y))
    add(keycaps, "Keycap_" + n, make_keycap(x, y))

doc.recompute()
doc.saveAs(os.path.join(OUT, "g2pad.FCStd"))

# ---- STEP exports
stepdir = os.path.join(OUT, "step")
os.makedirs(stepdir, exist_ok=True)
Import.export([tray], os.path.join(stepdir, "g2pad_bottom_tray.step"))
Import.export([plate], os.path.join(stepdir, "g2pad_top_plate.step"))
Import.export([doc.getObject("Keycap_Back_Q")], os.path.join(stepdir, "g2pad_keycap_reference.step"))
Import.export([enclosure, electronics, keycaps], os.path.join(OUT, "g2pad_assembly.step"))

# ---- meshes for README renders
import Mesh, MeshPart
meshdir = os.path.join(OUT, "..", "docs", "render", "mesh")
os.makedirs(meshdir, exist_ok=True)
for o in doc.Objects:
    if o.TypeId == "Part::Feature":
        m = MeshPart.meshFromShape(Shape=o.Shape, LinearDeflection=0.08, AngularDeflection=0.3)
        m.write(os.path.join(meshdir, o.Name + ".stl"))

# ---- interference check between printed parts and electronics
probs = []
solids = {o.Name: o.Shape for o in doc.Objects if o.TypeId == "Part::Feature"}
for a in ("BottomTray", "TopPlate"):
    for bname, bs in solids.items():
        if bname in ("BottomTray", "TopPlate") or bname.startswith("Keycap"):
            continue
        v = solids[a].common(bs).Volume
        if v > 0.05:
            probs.append((a, bname, round(v, 2)))
print("INTERFERENCE", probs)
print("OUTER", round(OUT_W, 1), "x", round(OUT_H, 1), "x", round(PLATE_TOP, 1), "mm (without keycaps)")
