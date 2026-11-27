# G2Pad

G2Pad is a four-key Bluetooth macro pad for the Even Realities G2 smart glasses with fast command input and direct control of the glasses's interface. 

![alt text](https://github.com/user-attachments/assets/47bf8b6d-8a2d-46ce-bc89-58d27798a111)

p.s. apologies for the sometimes fuzzy quality of my visuals and posters- I screenshotted them directly from Canva


G2Pad was designed to use four official GitHub keycaps which requires MX-style mechanical switches. The goal of G2Pad is to create a cheaper alternative to the glasses' existing touch and ring controls, as the glasses alone cost upwards of 600 bucks with prescriptions and an extra $300 for the gadget 'R1 ring.' Using a macro pad for control allows for better physical feedback as well. 

The main personal reason I built G2Pad was also to show my dad the product of his monetary investment in me in the form of a dedicated electronics build for him and also to repay him for paying for these expensive smart glasses. 

Also special thanks to my teachers and friends involved in helping me develop these visuals and posters!!

![alt text](https://github.com/user-attachments/assets/dd0a4980-03c4-444c-b44a-beb6f59d9100)

## How to use G2Pad
1. slide the left switch to ON
2. on your phone, open bluetooth and pair with 'G2Pad' 
3. open an Even Hub app on your phone that listens for G2Pads keys (this is the part im building next after funding and hardware)
4. use the four keys to move around the glasses (controls listed below under 'controls')
5. to charge, plug a usb-c cable into the XIAO with the power switch to ON
## Features
+ 4 MX-style mechanical switches
+ Seeed Studio XIAO nRF52840 with Bluetooth Low Energy
+ 150 mAh LiPo battery- charges with USB-C
+ On/Off slide switch
+ Auto Sleep functionality
+ Custom 42 x 64 mm PCB
+ 3D printed 47 x 69 x 16 mm case with a lanyard hole
+ Open source ZMK firmware

## Controls

Each key has a dedicated message that directs to the phone in the form of a letter. The keys 'back' and 'select' specifically do a second function if held down for longer than 0.4 seconds. Each keys control is as follows:
![alt text](https://github.com/user-attachments/assets/1697c8b1-39ff-40a6-b662-c4461c66dec5)
There are also two combos:
+ pressing 'up' and 'down' together turns Nav mode on or off, which changes the keys to arrows enter and esc
+ holding 'back' and 'select' together opens the Bluetooth function, which makes 'up' the button to switch to the next paired device and then 'down' to forget the current pairing

### How G2Pad works
G2Pad doesn't take keyboard input on its own, so I made the glasses-connected phone sort of like a middleman which connects to both the glasses and G2Pad via standard Bluetooth HID. The Even Realities app will capture these keystrokes and send corresponding commands to teh glasses over bluetooth. 
The Even Hub app hasn't been built yet, but after I receive funding that will be my next step!
## Case
The case was modeled in FreeCAD and was designed to be printed in 2 parts:
+ the bottom tray, which holds the battery under the PCB and has three standoffs, the USB-C opening, the slot for the power switch, and the lanyard hole
+ the top plate, which is a 1.5 mm switch plate with screw bosses, a pocket for the XIAO underneath, and a recess for a name badge

![alt text](https://github.com/user-attachments/assets/e35418f9-23de-4c82-9ecc-6cf1dec9b990)
The parts are held together with three M2 x 12 mm screws that go up thru the tray and the PCB into the top plate. 
## PCB
Using KiCAD, the PCB ended up being 2 layers with a ground pour on both sides. The XIAO will be soldered onto the board at the bottom, and I'll put the four switches above the XIAO. The power switch is on the left edge of the first image attached here, and the battery plugs into a JST connector on the back of the board.
![alt text](https://github.com/user-attachments/assets/426ec0ae-0493-4c13-ac2d-478d98245e0a)
two short wires connect the board to the BAT+ and BAT- pads on the underside of the XIAO. 
![alt text](https://github.com/user-attachments/assets/0f2e76c9-c04b-41d9-80a6-df2e9c683af1)
the gerbers are in pcb/gerbers.zip and can be ordered from JLCPCB.
## Schematic
![alt text](https://github.com/user-attachments/assets/02b61150-ff1e-4c01-9b13-806c83bd9e45)

## Firmware
G2Pad's firmware runs on ZMK, which is open source firmware for wireless keyboards. I didn't compile the firmware on my own mac either so instead I made a Github actions workflow. To change what the keys do, edit firmware/g2pad.keymap.


## Bill of Materials
The parts come out to about $168 without tools and $263.10 with tools and shipping. See [BOM.csv](BOM.csv) for the full list of parts

## Build Steps

1. get all materials from the bom and order them (including the pcb from JLCPCB) then 3d the bottom and top trays
2. clean up the prints
3. soldering!! i will finish this section once i actually get my hardware but from my understanding ill def have to solder the BAT pads on the XIAO then solder the XIAO to the board
4. put the MK switches into the top plate then line the pins up with the pcb then solder them in
5. flash the firmware 
6. set the LiPo into the tray and plug into the JST socket
7. screwing!! line up the pcb and plate and screw everything tg
8. press on the four keycaps
9. Done! pair 'g2pad' over bluetooth to the phone and start clicking thru ur g2.

## Credits

Inspired by Ben Vallack, a developer on YouTube who created his own macro pad for his Even Realities G2 glasses. None of his code is open-sourced and most of his tutorials and methodology are locked behind paywalls anyways. No tutorials were followed.

The XIAO nRF52840 and the glasses in my posters are placeholders. Keycaps by [Github](https://thegithubshop.com/products/1542509-00-key-caps-assorted-pack-of-8), firmware by [ZMK](https://zmk.dev/).

