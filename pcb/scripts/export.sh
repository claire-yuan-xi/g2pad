#!/bin/sh
# Regenerate gerbers.zip, drill files and the PCB STEP. Run from the repo root (KiCad 7+).
set -e
cd pcb
rm -rf gerbers && mkdir gerbers
kicad-cli pcb export gerbers -o gerbers/ --layers F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts --subtract-soldermask g2pad.kicad_pcb
kicad-cli pcb export drill -o gerbers/ --format excellon --excellon-separate-th --generate-map --map-format gerberx2 g2pad.kicad_pcb
rm -f gerbers.zip && (cd gerbers && zip -q ../gerbers.zip *)
kicad-cli pcb export step --subst-models -f -o ../cad/step/g2pad_pcb.step g2pad.kicad_pcb
kicad-cli sch export pdf -o g2pad_schematic.pdf g2pad.kicad_sch
