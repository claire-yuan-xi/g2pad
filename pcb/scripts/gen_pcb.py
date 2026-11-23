#!/usr/bin/python3
"""Generate pcb/g2pad.kicad_pcb (KiCad 7) for G2Pad: placement, routing, GND pours.

Run with KiCad's Python (needs the `pcbnew` module), from the repo root:
    /usr/bin/python3 pcb/scripts/gen_pcb.py
Footprints link to the schematic symbols, so "Update PCB from Schematic" in
KiCad matches everything up.
"""
import json, os
import pcbnew
from pcbnew import VECTOR2I, FromMM as MM

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.dirname(HERE)
FPDIR = os.environ.get("KICAD7_FOOTPRINT_DIR", "/usr/share/kicad/footprints")
SYM = json.load(open(os.path.join(HERE, "symbol_uuids.json")))

X0, Y0, W, H = 100.0, 100.0, 42.0, 64.0  # board outline (mm)
PITCH = 19.05
KC = {  # key centres
    "SW1": (X0 + 21 - PITCH / 2, 111.5),
    "SW2": (X0 + 21 + PITCH / 2, 111.5),
    "SW3": (X0 + 21 - PITCH / 2, 111.5 + PITCH),
    "SW4": (X0 + 21 + PITCH / 2, 111.5 + PITCH),
}
FUNC = {"SW1": "BACK Q", "SW2": "UP W", "SW3": "SELECT E", "SW4": "DOWN S"}

b = pcbnew.BOARD()
ds = b.GetDesignSettings()
ds.SetCopperLayerCount(2)
ds.m_TrackMinWidth = MM(0.2)
ds.m_MinClearance = MM(0.2)
ds.SetAuxOrigin(VECTOR2I(MM(X0), MM(Y0 + H)))
ds.SetGridOrigin(VECTOR2I(MM(X0), MM(Y0)))
tb = b.GetTitleBlock()
tb.SetTitle("G2Pad")
tb.SetRevision("1.0")
tb.SetDate("2026-11-23")
tb.SetCompany("claire-yuan-xi")

nets = {}


def net(name):
    if name not in nets:
        n = pcbnew.NETINFO_ITEM(b, name)
        b.Add(n)
        nets[name] = n
    return nets[name]


def add_fp(lib, name, ref, value, x, y, rot=0, padnets=None, side_back=False):
    libpath = os.path.join(PCB, "lib", "G2Pad.pretty") if lib == "G2Pad" else os.path.join(FPDIR, lib + ".pretty")
    fp = pcbnew.FootprintLoad(libpath, name)
    fp.SetReference(ref)
    fp.SetValue(value)
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    fp.SetPosition(VECTOR2I(MM(x), MM(y)))
    fp.SetOrientationDegrees(rot)
    if ref in SYM:
        fp.SetPath(pcbnew.KIID_PATH("/" + SYM[ref]))
    b.Add(fp)
    for p in fp.Pads():
        if padnets and p.GetNumber() in padnets:
            p.SetNet(net(padnets[p.GetNumber()]))
    return fp


def pad(fp, num):
    for p in fp.Pads():
        if p.GetNumber() == num:
            q = p.GetPosition()
            return (pcbnew.ToMM(q.x), pcbnew.TOMM(q.y)) if False else (q.x / 1e6, q.y / 1e6)
    raise KeyError(num)


def track(pts, netname, layer=pcbnew.B_Cu, w=0.3):
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(VECTOR2I(MM(x1), MM(y1)))
        t.SetEnd(VECTOR2I(MM(x2), MM(y2)))
        t.SetWidth(MM(w))
        t.SetLayer(layer)
        t.SetNet(net(netname))
        b.Add(t)


def via(x, y, netname="GND"):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(VECTOR2I(MM(x), MM(y)))
    v.SetDrill(MM(0.4))
    v.SetWidth(MM(0.8))
    v.SetNet(net(netname))
    b.Add(v)


def line(x1, y1, x2, y2, layer=pcbnew.Edge_Cuts, w=0.1):
    s = pcbnew.PCB_SHAPE(b)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(VECTOR2I(MM(x1), MM(y1)))
    s.SetEnd(VECTOR2I(MM(x2), MM(y2)))
    s.SetLayer(layer)
    s.SetWidth(MM(w))
    b.Add(s)


def arc(cx, cy, sx, sy, angle):
    s = pcbnew.PCB_SHAPE(b)
    s.SetShape(pcbnew.SHAPE_T_ARC)
    s.SetCenter(VECTOR2I(MM(cx), MM(cy)))
    s.SetStart(VECTOR2I(MM(sx), MM(sy)))
    s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(angle, pcbnew.DEGREES_T), True)
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetWidth(MM(0.1))
    b.Add(s)


def text(s, x, y, size=1.0, layer=pcbnew.F_SilkS, mirror=False):
    t = pcbnew.PCB_TEXT(b)
    t.SetText(s)
    t.SetPosition(VECTOR2I(MM(x), MM(y)))
    t.SetLayer(layer)
    t.SetTextSize(VECTOR2I(MM(size), MM(size)))
    t.SetTextThickness(MM(size * 0.15))
    if mirror:
        t.SetMirrored(True)
    b.Add(t)


# ---- outline: rounded rectangle, r = 3 mm
r = 1.5
x1, y1, x2, y2 = X0, Y0, X0 + W, Y0 + H
line(x1 + r, y1, x2 - r, y1); line(x2, y1 + r, x2, y2 - r)
line(x2 - r, y2, x1 + r, y2); line(x1, y2 - r, x1, y1 + r)
arc(x1 + r, y1 + r, x1, y1 + r, 90)
arc(x2 - r, y1 + r, x2 - r, y1, 90)
arc(x2 - r, y2 - r, x2, y2 - r, 90)
arc(x1 + r, y2 - r, x1 + r, y2, 90)

# ---- key switches. MX footprint origin is pin 1; switch centre is at (-2.54, +5.08) from it.
sig = {"SW1": "K_BACK", "SW2": "K_UP", "SW3": "K_SELECT", "SW4": "K_DOWN"}
sw = {}
for ref, (cx, cy) in KC.items():
    sw[ref] = add_fp("Button_Switch_Keyboard", "SW_Cherry_MX_1.00u_PCB", ref, "MX_Switch",
                     cx + 2.54, cy - 5.08, 0, {"1": sig[ref], "2": "GND"})
    text(FUNC[ref], cx, cy + 9.4, 0.9)

# ---- XIAO, USB-C facing the bottom board edge
XC = (X0 + 21, Y0 + H - 11.5)
u1 = add_fp("G2Pad", "XIAO_nRF52840_SMD", "U1", "XIAO_nRF52840", XC[0], XC[1], 180,
            {"11": "K_BACK", "10": "K_SELECT", "5": "K_UP", "6": "K_DOWN", "13": "GND"})

u1.Reference().SetPosition(VECTOR2I(MM(XC[0]), MM(XC[1] - 2)))
u1.Value().SetVisible(False)

# ---- power: side-actuated slide switch on the left edge, JST-PH battery socket, wire pads to XIAO BAT pads
sw5 = add_fp("Button_Switch_SMD", "SW_SPDT_PCM12", "SW5", "Power (PCM12)", X0 + 2.9, 158.0, 270,
             {"1": "VBAT", "2": "BAT_RAW"})
j1 = add_fp("Connector_JST", "JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical", "J1", "LiPo (JST-PH)", 109.0, 155.6, 270,
            {"1": "BAT_RAW", "2": "GND"})
j1.Flip(j1.GetPosition(), False)  # socket on the back, beside the LiPo (front side has no height for it)
j2 = add_fp("Connector_PinHeader_2.54mm", "PinHeader_1x02_P2.54mm_Vertical", "J2", "BAT wires", 133.0, 159.0, 180,
            {"1": "VBAT", "2": "GND"})

# ---- mounting holes
holes = [(X0 + 2.6, Y0 + 2.6), (X0 + W - 2.6, Y0 + 2.6), (X0 + W - 3.5, Y0 + H - 3.5)]
for i, (hx, hy) in enumerate(holes):
    add_fp("MountingHole", "MountingHole_2.2mm_M2", f"H{i+1}", "M2", hx, hy)

# ---- routing (B.Cu for keys)
def key_route(swref, xiao_pad, xcol, netname, via_x):
    p = pad(sw[swref], "1"); d = pad(u1, xiao_pad)
    track([p, (xcol, p[1]), (xcol, d[1]), (via_x, d[1])], netname)
    via(via_x, d[1], netname)
    track([(via_x, d[1]), d], netname, pcbnew.F_Cu)


key_route("SW1", "11", 101.6, "K_BACK", 110.4)
key_route("SW3", "10", 104.0, "K_SELECT", 110.4)
key_route("SW2", "5", 140.4, "K_UP", 131.6)
key_route("SW4", "6", 138.0, "K_DOWN", 131.6)
# battery (F.Cu)
a = pad(sw5, "2"); c = pad(j1, "1")
track([a, (c[0] - 2.2, a[1]), (c[0] - 2.2, c[1]), c], "BAT_RAW", pcbnew.F_Cu, 0.5)
a = pad(sw5, "1"); c = pad(j2, "1")
track([a, (105.7, a[1])], "VBAT", pcbnew.F_Cu, 0.5)
via(105.7, a[1], "VBAT")
track([(105.7, a[1]), (105.7, 162.7), (c[0], 162.7), c], "VBAT", pcbnew.B_Cu, 0.5)

# ---- GND pours on both layers
for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    z = pcbnew.ZONE(b)
    z.SetLayer(layer)
    z.SetNet(net("GND"))
    z.SetLocalClearance(MM(0.3))
    z.SetMinThickness(MM(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(MM(0.5))
    z.SetThermalReliefSpokeWidth(MM(0.5))
    ol = z.Outline()
    ol.NewOutline()
    for (x, y) in [(X0 + 0.3, Y0 + 0.3), (X0 + W - 0.3, Y0 + 0.3), (X0 + W - 0.3, Y0 + H - 0.3), (X0 + 0.3, Y0 + H - 0.3)]:
        ol.Append(MM(x), MM(y))
    b.Add(z)
for (vx, vy) in [(121.0, 103.0), (121.0, 121.0), (121.0, 140.2), (110.0, 140.2), (132.0, 140.2), (135.5, 161.2), (105.5, 120.5)]:
    via(vx, vy)

# ---- silkscreen
text("G2Pad v1.0", X0 + 21, 125.0, 1.2, pcbnew.B_SilkS, True)
text("for Even Realities G2", X0 + 21, 102.2, 0.8)
text("ON/OFF", X0 + 3.2, 152.0, 0.8)
text("LiPo", 107.2, 152.2, 0.8)
text("BAT", 136.0, 157.7, 0.8)
text("G2Pad / claire-yuan-xi", X0 + 21, 118.0, 1.0, pcbnew.B_SilkS, True)
text("XIAO BAT+ -> J2 pin 1, BAT- -> pin 2", X0 + 21, 160.0, 0.8, pcbnew.B_SilkS, True)

out = os.path.join(PCB, "g2pad.kicad_pcb")
b.Save(out)
# zone fill is more reliable on a board loaded from disk
b = pcbnew.LoadBoard(out)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(out)
print("saved", out)
