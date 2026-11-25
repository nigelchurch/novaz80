# NOVAZ80 I/O Board 2 (PPI + LCD) — V102-IO2-0 (Rev 000)

Design analysis from `V102-IO2-0.net` (KiCad/Eeschema 9.0.7 export, 2026-11-25), the schematic (single sheet, `V102-IO2-0.kicad_sch`), the BoM and the PCB file (`V102-IO2-0.kicad_pcb`). The netlist and the PCB's pad-to-net connectivity were compared pad by pad (217 pads) and are identical. DRC: 0 violations, 0 unconnected pads, 0 footprint errors.

Title block: *NOVA Z80 Project – v102-IO2*, NOVA Embedded Solutions, drawn 2023-05-22, Rev 000. No revision notes on the schematic. The only text note is "BYPASS CAPACITORS".

PLD: `V102-IO2-00.PLD` and `V102-IO2-00.jed`. The fuse map was decoded and matches the source equations (section 7).

This is a different board from the main I/O board `V102-IO1-0` (Zilog PIO/CTC/SIO, USB serial, PS/2). The two can be fitted together: their port addresses don't overlap.

---

## 0. Where this board sits in the NOVAZ80 project

A simple user-interface and parallel-I/O board. It adds:
- an **82C55A PPI**: ports A and B (16 lines) go to a 2×16 edge connector; port C reads **8 push buttons**,
- a **20 × 4 character LCD** (HD44780-compatible module) driven directly from the bus in 8-bit mode, with a contrast trimmer.

The LCD covers most of the board's top side, so in practice this is the **top board of the stack** (section 6.1).

It uses no interrupts, takes no part in the daisy chain, and needs nothing Z80-specific apart from `IORQB`, `RDB` and `WRB`, so it works with the Z80, 6502 and MTX CPU boards. It takes +5 V from the stack and has no power supply of its own.

Status: built. Whether the LCD has been run on the Z80 SBC is still to confirm (section 10). Section 9 collects observations for the planned 4-layer revision.

---

## 1. Summary

| Item | Value |
|---|---|
| Parallel I/O | 82C55A PPI: port A, port B → J5 (2×16 right-angle socket); port C ← 8 buttons |
| Display | 20 × 4 character LCD module (HD44780-compatible), 8-bit bus, `RS` = A0, `R/W` = `WRB`, `E` from the PLD |
| Buttons | SW0–SW7, to +5 V, 10 k pull-downs (RN1): **pressed = 1** on PC0–PC7 |
| Glue | GAL16V8 PLD (I/O decode, simple mode), 74LVC2G14 (`RSTB` → 82C55 `RESET` inversion) |
| I/O ports | `24h`–`27h` 82C55, `30h`–`31h` LCD |
| Interrupts | None (`INTB` not used) |
| Power | +5 V from the stack (SPEC pin 2). LCD backlight wired straight to +5 V |
| PCB | 100 × 100 mm, 2-layer, +5 V pour on F.Cu, GND pour on B.Cu, 0.15 mm signal tracks (0.3 mm for some power), 59 vias |

---

## 2. Block diagram

```
          ┌──────── stack bus: A0–A7, D0–D7, IORQB, RDB, WRB, RSTB, +5V ────────┐
          │                                                                     │
 A0–A7, IORQB ─► PLD IC1 ─┬─► 8255CS (24–27, active low) ─► 82C55 /CS
                          └─► LCD    (30–31, active high) ─► LCD E

 D0–D7 ─────────┬─► 82C55 D0–D7          (A0, A1, /RD, /WR from the bus)
                └─► LCD d0–d7            (RS = A0, R/W = WRB)

 RSTB ─► IC3 inv ─► R82 ─► 82C55 RESET (active high)

 82C55 PA0–PA7, PB0–PB7 ─► J5 odd pins (even pins GND)
 82C55 PC0–PC7 ◄─ SW0–SW7 to +5V, RN1 10k pull-downs to GND

 RV1 10k: GND ─ wiper ─► LCD VO ─ +5V          LCD A (backlight) = +5V, K = GND
```

---

## 3. Parts (BoM)

| Ref | Part | Function | Datasheet |
|---|---|---|---|
| IC1 | GAL16V8, DIP-20 | I/O decode PLD | [ATF16V8B (compatible)](http://ww1.microchip.com/downloads/en/devicedoc/atmel-0364-pld-atf16v8b-8bq-8bql-datasheet.pdf) |
| IC2 | 82C55A, DIP-40 (maker not recorded) | Programmable peripheral interface | [82C55A (Intersil/Renesas)](https://www.renesas.com/82C55A), [82C55A (Intel)](https://www.profesores.frc.utn.edu.ar/electronica/tecnicasdigitalesii/Practicos/PlacaIO8bit/82c55.pdf) |
| IC3 | 74LVC2G14, SOT-23-6 | Schmitt inverter: `RSTB` → 82C55 `RESET` (second gate unused, input grounded) | [SN74LVC2G14](https://www.ti.com/lit/ds/symlink/sn74lvc2g14.pdf) |
| M1 | 20 × 4 character LCD module ("2004"), 16-pin header + 4 mounting holes | Display | [HD44780U controller](https://www.sparkfun.com/datasheets/LCD/HD44780.pdf) |
| RV1 | 10 k linear trimmer, Runtron RM-065 vertical | LCD contrast | — |
| RN1 | 10 k × 8, SIP-9 bussed | Button pull-downs (common to GND) | — |
| SW0–SW7 | Push buttons, Nidec Copal SH-7040B footprint | User buttons | — |
| J5 | 2×16 socket, 2.54 mm, right-angle | Ports A and B | — |
| J1–J4, J11, J22, J33, J44 | 8-way "11 mm" stacking sockets (bottom side) | Stack bus (section 6) | — |
| C4–C8 | 1 µF 1206 | +5 V bypass | — |

The schematic's datasheet field for IC2 points to the Intel NMOS 8255A, not the 82C55A.

---

## 4. Subsystems

### 4.1 Address decode (IC1)
See section 7. Both selects are I/O only (`/IORQ`), 8-bit decode (A0–A7). The PLD sees **no** `/RD`, `/WR` or `/M1`.

### 4.2 82C55A PPI (IC2)
- `A0`, `A1` from the bus: `24h` port A, `25h` port B, `26h` port C, `27h` control.
- `/CS` = PLD `8255CS`. `/RD`, `/WR` = bus `RDB`, `WRB`.
- `RESET` (active high) = `RSTB` inverted by IC3. Reset sets all three ports to input, mode 0.
- **Port A** and **port B** → J5 (section 6.2). Any mode is possible in principle, but modes 1 and 2 need port C bits as handshake lines, and port C is hard-wired to the buttons. In practice **ports A and B are mode 0 only.**
- **Port C** = buttons (section 4.4). Keep both halves of port C as **inputs**.
- Typical mode word: `89h` = mode 0, port A out, port B out, port C in. `9Bh` (the reset state) = everything in.

### 4.3 LCD (M1)
- Standard 16-pin HD44780 interface, wired in **8-bit mode**:

| LCD pin | Signal | Source |
|---|---|---|
| 1 VSS | GND | |
| 2 VDD | +5 V | |
| 3 VO | contrast | RV1 wiper (RV1 ends on GND and +5 V) |
| 4 RS | A0 | bus |
| 5 R/W | `WRB` | bus |
| 6 E | `LCD` | PLD pin 16, active high |
| 7–14 d0–d7 | D0–D7 | bus, direct |
| 15 A | backlight anode | +5 V direct |
| 16 K | backlight cathode | GND |
| mounting holes | GND | |

- **Ports:** A0 picks the register, `WRB` picks the direction:

| Port | Read (`IN`) | Write (`OUT`) |
|---|---|---|
| `30h` | busy flag (bit 7) + address counter | instruction |
| `31h` | data (DDRAM/CGRAM) | data |

- `E` is high for as long as `/IORQ` is low on a `30h`/`31h` access. At 4 MHz that's about 600 ns, longer than the HD44780's 230 ns minimum `E` pulse.
- R/W comes from `WRB`, which on the Z80 falls and rises **at the same time as `/IORQ`**. That leaves almost no R/W set-up or hold time around `E` (section 8). On the 6502 SBC `WRB` is a level for the whole cycle, so there the timing is fine.
- **Busy flag:** reads work normally (R/W is high for the whole read), so software can poll `IN (30h)` bit 7 instead of using fixed delays.
- **20 × 4 DDRAM addresses:** line 1 `00h`, line 2 `40h`, line 3 `14h`, line 4 `54h` (set address = `80h` + address).
- **Initialisation** (8-bit): `38h` three times (with ≥ 4.1 ms, then ≥ 100 µs between the first ones, per the HD44780 data sheet), then `38h` function set (8-bit, 2-line mode = 4 lines on a 2004), `0Ch` display on, `01h` clear (1.52 ms), `06h` entry mode. There's no hardware reset to the LCD, so software init after every reset is the safe way.
- **Backlight:** A to +5 V, K to GND, no resistor on this board. It relies on the module's own series resistor (most 2004 modules have one, often marked R8 or R9). The backlight is always on (section 9, item 5).
- **Contrast:** RV1 sits at the top edge, above the LCD, so it's reachable with the board assembled.

### 4.4 Buttons (SW0–SW7)
- Each button connects its port C line to **+5 V**. RN1 (10 k bussed, common pin to GND) pulls each line low.
- **Pressed = 1, released = 0.** SWn → PCn (SW0 → PC0 … SW7 → PC7). Read all eight with `IN A,(26h)`.
- No debounce in hardware. Debounce in software (for example sample every 10–20 ms and accept a change after two equal samples).
- Bus-hold: some 82C55A makes (Intersil/Harris) have bus-hold circuits on the port pins that hold an input at its last level with up to a few hundred µA. A 10 k pull-down may not overcome that hold-high current, so a released button could keep reading 1. Intel's 82C55A and the Renesas MS/MQ82C55A variants have no bus-hold. Which make is fitted isn't recorded (section 9, item 3).

### 4.5 Reset
`RSTB` (bus CTRL pin 1, active low, from the CPU board) → IC3 gate 1 (Schmitt inverter) → net `R82` → 82C55 `RESET` (active high). IC3's second gate has its input grounded and its output open. The LCD and the PLD have no reset.

### 4.6 Power
- +5 V only, from SPEC pin 2. No regulator, no switch.
- Bypass: C4–C8 (1 µF 1206) for three ICs plus the LCD.
- Copper: +5 V pour on F.Cu, GND pour on B.Cu.

---

## 5. I/O map (from the PLD)

| Port | Read | Write | Device |
|---|---|---|---|
| `24h` | port A | port A | 82C55 |
| `25h` | port B | port B | 82C55 |
| `26h` | port C (buttons, pressed = 1) | port C (don't: inputs only) | 82C55 |
| `27h` | — (82C55 control can't be read back on most makes) | mode word / bit set-reset | 82C55 |
| `30h` | LCD busy flag + address | LCD instruction | LCD |
| `31h` | LCD data | LCD data | LCD |

- Decode is on A0–A7 only, so the map repeats for any value of A8–A15. `30h`/`31h` are fully decoded on A1–A7; `24h`–`27h` on A2–A7.
- 6502 SBC: CPU `7F24`–`7F27` and `7F30`–`7F31`.
- **No clash** with the ports known so far: Z80 SBC CTC `18h`–`1Bh`, PIO `20h`–`23h`; I/O board `05h`–`13h`; VDP board `00h`–`03h`, `06h`. The undocumented CFX board's PLD source puts its own 82C55 at `6Ch`–`6Fh`, also no clash.
- Not checked against the original MTX512 port map (`24h`–`27h` and `30h`–`31h` are outside the ports the NOVAZ80 MTX configuration uses so far).

---

## 6. Connectors

### 6.1 Stack bus and physical layout
One footprint per group, bottom side, same corner layout as the other boards. Every group passes through.

| Corner | Connectors |
|---|---|
| Top-left | J1 ADDR, J11 ADDR2 |
| Top-right | J2 SPEC, J22 PROG |
| Bottom-left | J4 DATA, J44 AUX (silkscreen "SPARE") |
| Bottom-right | J3 CTRL, J33 MTX |

| Conn | Name | Pins 1→8 | Use on this board |
|---|---|---|---|
| J1 | ADDR | A0 … A7 | A0–A7 → PLD; A0 → 82C55 A0 and LCD RS; A1 → 82C55 A1 |
| J11 | ADDR2 | A15 … A8 (reversed) | Pass-through |
| J4 | DATA | D0 … D7 | 82C55 and LCD |
| J3 | CTRL | RSTB, CLK, M1B, MREQB, IORQB, RDB, WRB, INTB | RSTB → IC3 → 82C55 RESET. IORQB → PLD. RDB → 82C55. WRB → 82C55 and LCD R/W. CLK, M1B, MREQB, INTB pass-through |
| J2 | SPEC | GND, +5V, VDPINTB, IEO1, IEO2, 4M, OUT0, KBDRST | +5 V **in**. Everything else pass-through |
| J22 | PROG | –, ROM7, BUSRQ, ROMWEX, ROMCSX, RESX, ROMOEX, PWR | Pass-through only (PWR carries 12 V from the CPU board) |
| J33 | MTX | P0 P1 P2 P3 R0 R1 R2 CPM | Pass-through |
| J44 | AUX | 8 × not connected | Pass-through |

Physical layout (front side):
- The **LCD module** covers roughly the top two-thirds of the board (about 99 × 61 mm on a 100 × 100 mm board), on its four GND mounting holes. **IC1 (GAL), IC2 (82C55), RN1 and J5 sit underneath it.** The LCD has to come off to swap or reprogram the GAL.
- The 8 buttons are in a row along the bottom edge, below the LCD. RV1 is at the top edge, above it.
- J5 points out of the **left edge**, under the LCD.
- With stacking sockets on the bottom and the LCD on top, nothing can stack above this board.

### 6.2 J5 — ports A and B (2×16 right-angle socket)
| Pins | Signal |
|---|---|
| 1, 3, 5 … 15 | PA0, PA1 … PA7 |
| 17, 19 … 31 | PB0, PB1 … PB7 |
| 2, 4 … 32 | GND |

No +5 V, no port C.

### 6.3 Other
| Ref | Use |
|---|---|
| M1 | LCD module, 16-pin single row (section 4.3) |
| RV1 | LCD contrast |
| SW0–SW7 | Buttons → PC0–PC7 |

No jumpers.

---

## 7. PLD (IC1, GAL16V8) — pin use

| Pin | Signal | Dir | Notes |
|---|---|---|---|
| 1 | A0 | in | |
| 2–8 | A1–A7 | in | `FIELD ADDR = [A7..A0]` |
| 9 | IORQB | in | |
| 11 | — | in | not connected (simple mode, plain input) |
| 12, 13, 14 | — | (input) | not connected, spare |
| 15 | 8255CS | out | 82C55 /CS, active low |
| 16 | LCD | out | LCD E, **active high** |
| 17, 18, 19 | — | (input) | not connected, spare |

Seven pins are spare. `RDB`, `WRB` and `M1B` are on the bus but not routed to the PLD.

Equations (WinCUPL, `Device g16v8a`; the `.jed` is simple mode, `g16v8as`):
```
LCD      = ADDR:[30..31] & !IORQB ;   /* E, active high: 30h-31h        */
!8255CS  = ADDR:[24..27] & !IORQB ;   /* /CS, active low: 24h-27h       */
```
- The fuse map (`.jed`, built 2023-07-22) was decoded: one product term per output, both match the source. `LCD` is active high (XOR bit 1), `8255CS` active low (XOR bit 0). Pins 15 and 16 are outputs, the other six I/O pins inputs. Simple mode (SYN = 1, AC0 = 0), signature "00". The `.PLD` file was saved later (2023-07-26) with the same logic.
- Source comment: "4 addresses after the lcd a,b,c,ctrl". The 82C55's ports actually sit **below** the LCD (`24h` < `30h`).
- Neither select is qualified by `/RD`, `/WR` or `/M1`. The 82C55 doesn't need it (it only acts on `/RD` or `/WR`), but the LCD does: section 9, item 1.

---

## 8. Timing notes

- **Decode delay:** GAL16V8 propagation (speed grade not recorded, typically 10–25 ns) between `/IORQ`/address and the selects. Z80 I/O cycles have an automatic wait state, so this is comfortable at 4 MHz.
- **LCD E pulse:** about 600 ns at 4 MHz (`/IORQ` low time), against 230 ns minimum. Cycle time between accesses is far above the 500 ns minimum.
- **LCD R/W set-up and hold on the Z80** (HD44780U at 5 V: t<sub>AS</sub> ≥ 40 ns, t<sub>AH</sub> ≥ 10 ns):
  - *Start of a write:* `/WR` and `/IORQ` fall together. E rises one PLD delay later, so R/W set-up is only 10–25 ns.
  - *End of a write:* `/WR` and `/IORQ` rise together. R/W goes **high (read) one PLD delay before E falls**, and the HD44780 latches write data on E's falling edge. Hold is negative.
  - `RS` (A0) and the data are fine: the Z80 keeps the address valid for the whole cycle and write data from T1 until after `/WR` rises.
  - Many HD44780 clones tolerate this, but it's outside the data sheet (section 9, item 2).
- **LCD reads:** data out within 160 ns of E rising. The Z80 samples on T3's falling edge, several hundred ns later. Fine.
- **82C55A writes** latch on `/WR` rising. `/CS` rises one PLD delay after `/IORQ`, so `/CS` and A0/A1 are held past `/WR` as the 82C55 requires. Z80 write data stays valid after `/WR` rises.
- **Interrupt acknowledge:** in a Z80 INTA cycle (`/M1` + `/IORQ` low), the address bus carries the PC. If its low byte is `30h` or `31h`, E rises with R/W high and the LCD drives the data bus while the interrupting device puts its vector there (section 9, item 1). The 82C55 also sees `/CS`, but `/RD` stays high, so it stays off the bus.
- **6502 SBC:** `IORQB` is PHI2-qualified (about 500 ns) and `WRB` is the CPU's R/W level for the whole cycle, so R/W set-up and hold around E are correct. The 6502 never does an INTA cycle.

---

## 9. Observations for the next revision

Most important first.

1. **LCD responds to interrupt acknowledge cycles.** E isn't qualified by `/M1` (or by `/RD`/`/WR`). In a Z80 machine using interrupts, each interrupt has about a 2-in-256 chance of being acknowledged while the PC's low byte is `30h`/`31h`. With a 50 Hz VDP interrupt that's about once every 2–3 seconds. The LCD then drives D0–D7 while the interrupting device puts its vector on the bus. In **IM 2** (or IM 0) that gives a corrupt vector and a jump to a random address; in IM 1 the vector is ignored and only the bus contention remains. The MTX configuration (IM 2, CTC vectors) is the most exposed.
   - Fix: route `RDB` and `WRB` (or `M1B`) to spare PLD inputs and use `LCD = ADDR:[30..31] & !IORQB & (!RDB # !WRB)`. INTA cycles have neither `/RD` nor `/WR`. Seven PLD pins are free, so on the current board this is two wires and a new `.jed`.
   - *To confirm:* whether the LCD has run on the Z80 SBC or the MTX with interrupts enabled.
2. **LCD R/W timing from `WRB` on the Z80** (section 8). Two cures:
   - R/W = **A1** (stable for the whole cycle): ports `30h` write instruction, `31h` write data, `32h` read status, `33h` read data. Widen the decode to `30h`–`33h`.
   - Or keep `WRB` and make E end before `/WR` rises (harder in a GAL with no clock). A1 is simpler.
3. **Buttons against the 82C55 port pins.**
   - **Bus-hold:** with an Intersil/Harris 82C55A, the hold-high current (up to a few hundred µA) can beat a 10 k pull-down, and a released button may read as pressed. If that's ever seen, it's this. Wire buttons to **GND with pull-ups** (or use 2k2 pull-downs) and record the 82C55 make.
   - **Short risk:** a button ties its line straight to +5 V. If port C (or one half of it) is ever set as an output driving low, pressing the button shorts the output. It can happen through a wrong mode word, or through random writes to `27h` while the programmer holds the bus on the 6502 SBC (6502 document, section 4.9). `RESX` → `RSTB` resets the 82C55 afterwards, which sets everything back to inputs. A 1 k series resistor per button, or buttons to GND, removes the risk.
   - **Handshake modes lost:** port C is the only source of the 82C55's mode 1/2 handshakes and `INTR` lines, so ports A and B are mode 0 only. Putting the buttons on port B and the handshakes on port C would keep those modes available.
4. **No interrupt from the buttons.** The CPU has to poll `26h`. If wanted, a button-change interrupt through the 82C55's mode 1 `INTR` (needs item 3's re-arrangement) or a separate open-drain `INTB` driver would do it.
5. **LCD backlight always on, no resistor on the board.** It depends on the module's own series resistor, which varies between makes (some have 0 Ω, some none fitted). Add a footprint for a series resistor and, ideally, a transistor switch on a spare 82C55 line or PLD-decoded latch bit so software can dim or turn it off. Note the backlight current (typically 20–100 mA) in the stack's power budget.
6. **Board must be top of the stack, and the LCD hides the GAL.** Reprogramming or swapping IC1 (or IC2) means removing the LCD. Move the GAL out from under the LCD, or socket the LCD on a header so it lifts off easily.
7. **Decode slack.** Only 2 of the GAL's 8 outputs are used. A latch for the backlight, LCD reset/power, or a second LCD E (for 40 × 4 modules that use two controllers) could be added at no cost.
8. **Decoupling.** Five 1 µF caps for three ICs plus the LCD is adequate here, but add 100 nF at the 82C55 and GAL as on the other boards' revision notes.
9. **Floating pins.** PLD pin 11 and the six unused I/O pins are unconnected. An ATF16V8B has pin keepers and Lattice GAL16V8D has internal pull-ups, so this is harmless with those makes. Tie pin 11 to GND or +5 V anyway.
10. **Housekeeping:**
    - The schematic's IC2 datasheet link is the Intel NMOS 8255A, not the 82C55A. The 82C55 make and the GAL speed grade aren't recorded.
    - The PLD source's `Company` field is `xxx`, and its comment says the 82C55 is *after* the LCD (it's before).
    - The folder holds `PHONO-SRC-00A-erc.rpt` (the name left over from another project, as on the other boards), an older `V102-IO2-0.kicad_sch-bak`, and two KiCad lock files (`~V102-IO2-0.kicad_pcb.lck`, `~V102-IO2-0.kicad_sch.lck`), so the project was open in KiCad when these files were read.

---

## 10. Open questions

- Has the LCD been run on the Z80 SBC and the MTX, and with interrupts enabled (items 1 and 2)?
- Which make of 82C55A is fitted, and does a released button always read 0 (item 3)?
- Which 2004 module is fitted (controller: HD44780, ST7066U, SPLC780…) and does it have a backlight series resistor?
- Ports `24h`–`27h` and `30h`–`31h` against the original MTX512 port map, in case MTX software or expansions expect something there.
