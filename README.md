# G2Pad

**A pocket-sized, four-key Bluetooth macro pad for the Even Realities G2 smart glasses.**

G2Pad gives the G2 a real, clicky, physical controller. Four official GitHub keycaps sit on MX switches in a 2×2 grid: **Back**, **Up**, **Select** and **Down**. It runs on a coin-sized Seeed XIAO nRF52840 with a tiny LiPo, so it lives in a pocket and works without looking at it.

![G2Pad assembled](docs/images/assembly.png)

| | |
|---|---|
| Size | 47 × 69 × 16 mm case (about 28 mm tall with keycaps) |
| Brain | Seeed Studio XIAO nRF52840 (Bluetooth LE 5, USB-C charging) |
| Keys | 4 × MX-style switches + official GitHub keycaps |
| Power | 150 mAh LiPo, on/off slide switch, charges over USB-C |
| Firmware | [ZMK](https://zmk.dev) (open-source wireless keyboard firmware) |
| Cost | about $56 in parts ([BOM.csv](BOM.csv)) |

## Why I made it

The G2 is controlled with taps and swipes on the temples or with the R1 smart ring. Those work, but they are fiddly when you are walking, wearing gloves, presenting, or trying to move through a long menu in a custom app. I wanted something I can feel in my pocket and press without looking: real keys with real travel, one job per key. Building it also lets me design my own Even Hub apps around a controller I know exactly.

## How to use it

1. Slide the power switch on the left side to **ON**.
2. On your phone, open Bluetooth settings and pair with **G2Pad** (it shows up like a keyboard).
3. Open a G2 app built to listen for G2Pad keys (see [How it talks to the glasses](#how-it-talks-to-the-glasses)).
4. Press keys:

```
 +-------------+-------------+
 |  BACK   (Q) |  UP     (W) |     tap:  send the letter
 |  hold: H    |             |     hold: long-press action
 +-------------+-------------+
 |  SELECT (E) |  DOWN   (S) |
 |  hold: M    |             |
 +-------------+-------------+
```

| Key | Tap | Hold (> 0.4 s) |
|---|---|---|
| Back (top-left) | `Q`, go back | `H`, go home |
| Up (top-right) | `W`, scroll / move up | |
| Select (bottom-left) | `E`, confirm | `M`, shortcut / menu |
| Down (bottom-right) | `S`, scroll / move down | |
| Up + Down together | toggle **Nav mode**: arrows, Enter, Esc | |
| Hold Back + Select | Bluetooth layer: Up = next paired device, Down = forget pairing | |

The keys send plain letters (Q, W, E, S) instead of special keys, which phones pass through more reliably. Charge it by plugging USB-C into the XIAO with the switch ON. After 15 minutes idle it sleeps, and any key wakes it.

## How it talks to the glasses

```
[G2Pad] --BLE keyboard (HID)--> [phone] --> [Even Hub app (web app in the Even app)] --Even Hub SDK--> [G2 display]
```

The G2 has no keyboard input of its own, so the phone is the bridge. G2Pad pairs with the phone as a normal Bluetooth keyboard. Even Hub apps are web apps that the Even Realities app runs in a WebView on the phone, and they draw to the glasses through the Even Hub SDK ([Even Hub architecture](https://hub.evenrealities.com/docs/get-started/architecture)). The plan is for my G2 app to listen for the Q/W/E/S key presses and turn them into G2 actions (scroll, select, back).

**Open question I'm testing first:** the official docs only describe input from the glasses' touchpads and the R1 ring. I have not found a public project that already drives G2 apps from a Bluetooth keyboard, so step one when parts arrive is to check that the Even app's WebView receives key presses. If it does not, the fallback is to have G2Pad's firmware advertise its own small BLE service that a companion app reads. Third-party projects such as [Faceclaw](https://github.com/jimrandomh/faceclaw), which adds a Wear OS watch as an extra remote, show that the G2 can take input from devices other than the ring. More G2 developer resources: [awesome-even-realities-g2](https://github.com/pangoleen/awesome-even-realities-g2).

## Design

### Schematic

![Schematic](docs/images/schematic.png)

Each switch connects one XIAO pin to ground and uses the chip's internal pull-up, so there is no matrix and no diodes.

| Key | XIAO pin | nRF52840 pin |
|---|---|---|
| SW1 Back | D10 | P1.15 |
| SW2 Up | D4 | P0.04 |
| SW3 Select | D9 | P1.14 |
| SW4 Down | D5 | P0.05 |

The LiPo plugs into a JST-PH socket (J1) on the back of the board. It goes through the slide switch (SW5) to two pads (J2), and two short wires connect J2 to the BAT+ / BAT− pads underneath the XIAO, which has its own charger.

### PCB

![PCB front and back](docs/images/pcb.png)

A 2-layer, 42 × 64 mm board with ground pours on both sides. The key signals run on the back layer, and the XIAO is surface-mounted by its castellated edges with USB-C at the board edge. The DRC report shows 0 errors and 0 unconnected pads. Fabrication files are in [`pcb/gerbers.zip`](pcb/gerbers.zip), ready to upload to JLCPCB or any other fab.

### Case

![Exploded view](docs/images/exploded.png)

Two 3D-printed parts:

* **Bottom tray**: holds the LiPo under the PCB, has three standoffs, a USB-C opening, a slot for the power switch, and a lanyard hole.
* **Top plate**: a 1.5 mm switch plate set at the MX standard height (5 mm above the PCB). It has screw bosses, plus a pocket on its underside for the XIAO.

Three M2 × 12 screws go up through the tray and the PCB into the plate bosses, clamping everything together. The FreeCAD build script checks for collisions between the printed parts and the electronics, and finds none.

![Inside the case](docs/images/internals.png)

## Repository layout

| Path | What's inside |
|---|---|
| [`cad/g2pad.FCStd`](cad/g2pad.FCStd) | FreeCAD source with the full assembly: enclosure, PCB, XIAO, switches, battery, keycaps |
| [`cad/g2pad_assembly.step`](cad/g2pad_assembly.step) | Full assembly as STEP |
| [`cad/step/`](cad/step) | STEP for each part: bottom tray, top plate, PCB, keycap reference |
| [`cad/build_g2pad.py`](cad/build_g2pad.py) | Parametric script that rebuilds the FreeCAD model and all STEP files |
| [`pcb/g2pad.kicad_pro`](pcb/g2pad.kicad_pro) | KiCad project (`.kicad_pro`, `.kicad_sch`, `.kicad_pcb`, `.kicad_prl`) |
| [`pcb/gerbers.zip`](pcb/gerbers.zip) | Gerbers and drill files for fabrication |
| [`pcb/g2pad_schematic.pdf`](pcb/g2pad_schematic.pdf) | Schematic as PDF |
| [`pcb/lib/`](pcb/lib) | Custom KiCad symbol and footprint for the XIAO nRF52840 |
| [`pcb/scripts/`](pcb/scripts) | Scripts that generate the schematic and board, and export the fab files |
| [`firmware/`](firmware) | ZMK config: shield, keymap, build matrix |
| [`BOM.csv`](BOM.csv) | Bill of materials with a link for every part |
| [`docs/`](docs) | README images and the three.js render page |

## Firmware

G2Pad runs ZMK as a custom shield (`g2pad`) on the `xiao_ble` board. The GitHub Actions workflow in [`.github/workflows/build.yml`](.github/workflows/build.yml) builds the firmware on every push. To flash it:

1. Download the `firmware` artifact from the latest Actions run.
2. Plug in G2Pad and double-tap the XIAO's reset button. A USB drive called `XIAO-SENSE` appears.
3. Drag the `.uf2` file onto the drive.

To change what the keys do, edit [`firmware/config/g2pad.keymap`](firmware/config/g2pad.keymap). The firmware has not been tested on hardware yet. This is a design submission, and the parts are not built yet.

## Bill of materials

See [BOM.csv](BOM.csv) for links. I don't own any of these parts yet.

| Part | Qty | ≈ Cost |
|---|---|---|
| Official GitHub keycaps | 1 set | $28.00 |
| Seeed XIAO nRF52840 | 1 | $9.90 |
| MX switches (5-pin) | 4 | $4.00 |
| 3.7 V 150 mAh LiPo (JST-PH) | 1 | $5.95 |
| JST-PH socket, PCM12 slide switch, wire, M2 screws | | $1.25 |
| PCB (5 pcs) + 3D printing | | $7.00 |
| **Total** | | **≈ $56 + shipping** |

## Build steps

1. Order the PCB (`pcb/gerbers.zip`) and print `cad/step/g2pad_bottom_tray.step` and `g2pad_top_plate.step` (PLA or PETG, 0.2 mm layers, no supports, with the plate printed top side down).
2. Solder the XIAO, the slide switch, the JST socket (on the back) and the J2 wires to the XIAO's BAT pads.
3. Snap the 4 switches into the top plate, then drop the plate onto the PCB and solder the switches.
4. Plug in the LiPo, set it in the tray, and screw the stack together with 3 × M2 screws from below.
5. Flash the firmware, put on the GitHub keycaps, and pair with your phone.

## Roadmap

- [x] Design: schematic, PCB, case, firmware, BOM
- [ ] Order parts, then check that the Even app WebView receives key presses
- [ ] Even Hub app that maps Q/W/E/S to G2 navigation
- [ ] Build, test daily, and polish
