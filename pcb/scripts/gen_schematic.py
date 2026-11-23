#!/usr/bin/env python3
"""Generate pcb/g2pad.kicad_sch (KiCad 7) for G2Pad.

The schematic is generated so it can be rebuilt from this script, but it is a
normal KiCad schematic: open it in KiCad 7+ and edit it like any other.
Run from the repo root:  python3 pcb/scripts/gen_schematic.py
"""
import os, re, uuid, json

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.dirname(HERE)
SYMDIR = os.environ.get("KICAD7_SYMBOL_DIR", "/usr/share/kicad/symbols")
NS = uuid.UUID("6b1f3c1e-2d0a-4c55-9a43-6a2f0b2a9d11")


def uid(name):
    return str(uuid.uuid5(NS, name))


ROOT = uid("root-sheet")

# ---------------------------------------------------------------- s-expr utils
def tokenize(s):
    return re.findall(r'"(?:\\.|[^"\\])*"|\(|\)|[^\s()"]+', s)


def parse(tokens, i=0):
    out = []
    while i < len(tokens):
        t = tokens[i]
        if t == "(":
            sub, i = parse(tokens, i + 1)
            out.append(sub)
        elif t == ")":
            return out, i + 1
        else:
            out.append(t)
            i += 1
    return out, i


def dump(e, ind=0):
    if not isinstance(e, list):
        return e
    if all(not isinstance(x, list) for x in e):
        return "(" + " ".join(e) + ")"
    s = "("
    for k, x in enumerate(e):
        if isinstance(x, list):
            s += "\n" + "  " * (ind + 1) + dump(x, ind + 1)
        else:
            s += (" " if k else "") + x
    return s + ")"


_libcache = {}


def lib_symbol(lib, name):
    if lib == "G2Pad":
        path = os.path.join(PCB, "lib", "G2Pad.kicad_sym")
    else:
        path = os.path.join(SYMDIR, lib + ".kicad_sym")
    if path not in _libcache:
        _libcache[path] = parse(tokenize(open(path).read()))[0][0]
    for e in _libcache[path]:
        if isinstance(e, list) and e[0] == "symbol" and e[1] == f'"{name}"':
            e = json.loads(json.dumps(e))
            e[1] = f'"{lib}:{name}"'
            return e
    raise KeyError(name)


def pins_of(sym):
    """{number: (x, y, angle)} in library coordinates (y up)."""
    pins = {}

    def walk(e):
        if isinstance(e, list):
            if e and e[0] == "pin":
                at = next(x for x in e if isinstance(x, list) and x[0] == "at")
                num = next(x for x in e if isinstance(x, list) and x[0] == "number")
                pins[num[1].strip('"')] = (float(at[1]), float(at[2]), float(at[3]))
            for x in e:
                walk(x)

    walk(sym)
    return pins


# ---------------------------------------------------------------- design
SYMS = {
    "sw": ("Switch", "SW_Push"),
    "spdt": ("Switch", "SW_SPDT"),
    "conn2": ("Connector_Generic", "Conn_01x02"),
    "hole": ("Mechanical", "MountingHole"),
    "gnd": ("power", "GND"),
    "xiao": ("G2Pad", "XIAO_nRF52840"),
}
LIB = {k: lib_symbol(*v) for k, v in SYMS.items()}
PINS = {k: pins_of(v) for k, v in LIB.items()}

parts = []   # (key, ref, value, footprint, x, y, extra_props)
labels = []  # (net, x, y, angle)
wires = []
power = []   # (x, y)
noconn = []
texts = []

KEYS = [  # ref, net, keycap function, position on pad
    ("SW1", "K_BACK", "Back (Q)", "top-left"),
    ("SW2", "K_UP", "Up (W)", "top-right"),
    ("SW3", "K_SELECT", "Select (E)", "bottom-left"),
    ("SW4", "K_DOWN", "Down (S)", "bottom-right"),
]


def g(v):
    return round(v / 1.27) * 1.27


def place(key, ref, value, fp, x, y, props=None):
    parts.append((key, ref, value, fp, g(x), g(y), props or {}))
    return g(x), g(y)


def pin_xy(key, x, y, num):
    px, py, a = PINS[key][num]
    return x + px, y - py, a


def stub(key, x, y, num, net=None, length=2.54, gnd=False):
    """Short wire out of a pin, ending in a net label or GND symbol."""
    import math
    px, py, a = pin_xy(key, x, y, num)
    dx, dy = -math.cos(math.radians(a)), math.sin(math.radians(a))
    ex, ey = round(px + dx * length, 2), round(py + dy * length, 2)
    wires.append((px, py, ex, ey))
    if gnd:
        if abs(dy) > 0.5 and dy < 0:  # pin points up: extend further and drop down
            ex2 = ex + 2.54
            wires.append((ex, ey, ex2, ey))
            ex = ex2
        power.append((ex, ey))
    elif net:
        ang = 180 if dx < -0.5 else 0
        labels.append((net, ex, ey, ang))


# Key switches
texts.append(("Key switches (MX, direct-wired, internal pull-ups)", 30.48, 33.02, 1.8))
for i, (ref, net, func, pos) in enumerate(KEYS):
    x, y = place("sw", ref, "MX_Switch", "Button_Switch_Keyboard:SW_Cherry_MX_1.00u_PCB",
                 45.72, 45.72 + i * 15.24, {"Function": func})
    stub("sw", x, y, "1", net, length=5.08)
    stub("sw", x, y, "2", gnd=True, length=5.08)
    texts.append((f"{func}, {pos}", x - 6.35, y + 8.89, 1.27))

# MCU
texts.append(("Seeed XIAO nRF52840 (BLE 5, ZMK)", 111.76, 33.02, 1.8))
ux, uy = place("xiao", "U1", "XIAO_nRF52840", "G2Pad:XIAO_nRF52840_SMD", 127, 63.5)
mcu_nets = {"11": "K_BACK", "10": "K_SELECT", "5": "K_UP", "6": "K_DOWN"}  # D10, D9, D4, D5
for num in PINS["xiao"]:
    if num in mcu_nets:
        stub("xiao", ux, uy, num, mcu_nets[num], length=5.08)
    elif num == "13":
        stub("xiao", ux, uy, num, gnd=True, length=5.08)
    else:
        px, py, _ = pin_xy("xiao", ux, uy, num)
        noconn.append((px, py))

# Power
texts.append(("Battery + power switch", 172.72, 33.02, 1.8))
jx, jy = place("conn2", "J1", "LiPo 3.7V (JST-PH)", "Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical",
               180.34, 53.34)
stub("conn2", jx, jy, "1", "BAT_RAW")
stub("conn2", jx, jy, "2", gnd=True)
sx, sy = place("spdt", "SW5", "Power (PCM12)", "Button_Switch_SMD:SW_SPDT_PCM12", 205.74, 53.34)
stub("spdt", sx, sy, "2", "BAT_RAW")
stub("spdt", sx, sy, "1", "VBAT")
px, py, _ = pin_xy("spdt", sx, sy, "3")
noconn.append((px, py))
kx, ky = place("conn2", "J2", "To XIAO BAT+/BAT- pads", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
               233.68, 53.34)
stub("conn2", kx, ky, "1", "VBAT")
stub("conn2", kx, ky, "2", gnd=True)
texts.append(("J2: two short wires from these pads to the BAT+ / BAT- pads\non the underside of the XIAO. The XIAO charges the LiPo over\nUSB-C while SW5 is ON.", 172.72, 71.12, 1.27))

# Mounting holes
texts.append(("M2 mounting holes", 172.72, 99.06, 1.8))
for i in range(3):
    place("hole", f"H{i+1}", "MountingHole_M2", "MountingHole:MountingHole_2.2mm_M2", 180.34 + i * 20.32, 106.68)

texts.append(("G2Pad: pocket BLE macro pad for Even Realities G2 glasses.\nKeys send Q / W / E / S over BLE HID to the phone; an Even Hub app maps them to G2 commands.",
              30.48, 124.46, 1.5))


# ---------------------------------------------------------------- write
def S(s):
    return '"' + s.replace('"', '\\"').replace("\n", "\\n") + '"'


out = []
out.append(f'(kicad_sch (version 20230121) (generator eeschema)')
out.append(f'  (uuid {ROOT})')
out.append('  (paper "A4")')
out.append('  (title_block (title "G2Pad") (date "2026-11-23") (rev "1.0") (company "claire-yuan-xi") (comment 1 "Pocket BLE macro pad for Even Realities G2"))')
out.append("  (lib_symbols")
for k in SYMS:
    out.append("    " + dump(LIB[k], 2))
out.append("  )")

for (x1, y1, x2, y2) in wires:
    out.append(f'  (wire (pts (xy {x1:.2f} {y1:.2f}) (xy {x2:.2f} {y2:.2f})) (stroke (width 0) (type default)) (uuid {uid(f"w{x1}{y1}{x2}{y2}")}))')
for (x, y) in noconn:
    out.append(f'  (no_connect (at {x:.2f} {y:.2f}) (uuid {uid(f"nc{x}{y}")}))')
for (net, x, y, a) in labels:
    just = "right" if a == 180 else "left"
    out.append(f'  (label {S(net)} (at {x:.2f} {y:.2f} {a}) (fields_autoplaced) (effects (font (size 1.27 1.27)) (justify {just} bottom)) (uuid {uid(f"l{net}{x}{y}")}))')
for (t, x, y, sz) in texts:
    out.append(f'  (text {S(t)} (at {x:.2f} {y:.2f} 0) (effects (font (size {sz} {sz})) (justify left bottom)) (uuid {uid("t" + t)}))')


VOFF = {"G2Pad:XIAO_nRF52840": 13, "Connector_Generic:Conn_01x02": 8.89, "Switch:SW_SPDT": 7.62}


def sym_instance(lib_id, ref, value, fp, x, y, props, pins, in_bom=True):
    u = uid("sym" + ref)
    r = [f'  (symbol (lib_id {S(lib_id)}) (at {x:.2f} {y:.2f} 0) (unit 1) (in_bom {"yes" if in_bom else "no"}) (on_board yes) (dnp no)',
         f'    (uuid {u})',
         f'    (property "Reference" {S(ref)} (at {x:.2f} {y - 6.35:.2f} 0) (effects (font (size 1.27 1.27))))',
         f'    (property "Value" {S(value)} (at {x:.2f} {y + VOFF.get(lib_id, 3.81):.2f} 0) (effects (font (size 1.27 1.27))))',
         f'    (property "Footprint" {S(fp)} (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) hide))',
         f'    (property "Datasheet" "~" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) hide))']
    for k, v in props.items():
        r.append(f'    (property {S(k)} {S(v)} (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) hide))')
    for p in pins:
        r.append(f'    (pin {S(p)} (uuid {uid(ref + "pin" + p)}))')
    r.append(f'    (instances (project "g2pad" (path "/{ROOT}" (reference {S(ref)}) (unit 1))))')
    r.append("  )")
    return r, u


refmap = {}
for (key, ref, value, fp, x, y, props) in parts:
    lib_id = ":".join(SYMS[key])
    r, u = sym_instance(lib_id, ref, value, fp, x, y, props, PINS[key].keys())
    out += r
    refmap[ref] = u

for i, (x, y) in enumerate(power):
    ref = f"#PWR0{i + 1:02d}"
    u = uid("pwr" + ref)
    out += [f'  (symbol (lib_id "power:GND") (at {x:.2f} {y:.2f} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no)',
            f'    (uuid {u})',
            f'    (property "Reference" {S(ref)} (at {x:.2f} {y + 6.35:.2f} 0) (effects (font (size 1.27 1.27)) hide))',
            f'    (property "Value" "GND" (at {x:.2f} {y + 3.81:.2f} 0) (effects (font (size 1.27 1.27))))',
            f'    (property "Footprint" "" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) hide))',
            f'    (property "Datasheet" "" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) hide))',
            f'    (pin "1" (uuid {uid(ref + "p1")}))',
            f'    (instances (project "g2pad" (path "/{ROOT}" (reference {S(ref)}) (unit 1))))',
            "  )"]

out.append(f'  (sheet_instances (path "/" (page "1")))')
out.append(")")
open(os.path.join(PCB, "g2pad.kicad_sch"), "w").write("\n".join(out) + "\n")
json.dump(refmap, open(os.path.join(HERE, "symbol_uuids.json"), "w"), indent=1)
print("wrote g2pad.kicad_sch with", len(parts), "parts")
