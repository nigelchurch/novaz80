# NOVAZ80 VDP + Sound Board — V102-VDP-1 (Rev 001)

Design analysis from `V102-VDP-1.net` (KiCad/Eeschema 9.0.7 export, 2026-11-25), the schematic (root sheet + `v102-con-z80.kicad_sch` CONNECTORS sheet), the BoM and the PCB file (`V102-VDP-1.kicad_pcb`). ERC: 0 errors / 0 warnings. DRC: 0 violations, 0 unconnected pads, 0 footprint errors.

Title block: *NOVAZ80 Project – V102-VDP*, NOVA Embedded Solutions, drawn 2023-07-07, Rev 001.
Revision note: 1. Reconfigured off-board pins on PLD for standardisation.

PLD: `V102-VDP-00.PLD` and `V102-VDP-00.jed`. The fuse map was decoded and matches the source equations (section 7).

---

## 0. Where this board sits in the NOVAZ80 project

The shared video and sound board. It adds:
- a **TMS9929A** (PAL, 50 Hz, component) or **TMS9918A** (NTSC, 60 Hz, composite) VDP with **16 KB of static VRAM** in place of the eight 4116 DRAMs the chip was designed for,
- an **SN76489** sound generator, written through a data latch and a self-timed strobe,
- four RCA sockets: **AUDIO** and three video sockets whose use depends on the VDP fitted (section 4.3),
- the **4 MHz oscillator** that drives the bus `4M` line,
- the **`OUT0`** strobe (`OUT (00h)`) for the MTX board's page latch.

Its ports (00h–03h, 06h) follow the Memotech MTX512 map. In the MTX configuration this board is required, partly because it supplies `OUT0`.

The VDP interrupt leaves on `VDPINTB` only. It reaches the CPU through the I/O board's CTC channel 0 (V102-IO1-0). This board is not in the Zilog daisy chain and doesn't drive `INTB`.

It takes +5 V from the stack and has no power supply of its own.

Status: built, tested and in use. Section 9 collects observations for the planned 4-layer revision.

---

## 1. Summary

| Item | Value |
|---|---|
| Video | TMS9929A (Y / R-Y / B-Y) or TMS9918A (composite) VDP, 10.7386 MHz crystal. Picture taken from J3 in both cases |
| VRAM | HM62256 32 K × 8 SRAM, 16 K used (A14 grounded), behind 3 × 74HC574 latches |
| Sound | SN76489, 4 MHz clock, AC-coupled to an RCA socket |
| Glue | GAL16V8 PLD: I/O decode only. 74HC14 for VRAM strobe inversion/delay |
| I/O ports | `00h` W (OUT0), `01h` VDP data, `02h` VDP control/status, `03h` R (sound strobe), `06h` W (sound data) |
| Clock out | XT1 4 MHz can → bus `4M` (SPEC pin 6) and SN76489 |
| Power | +5 V from the stack (SPEC pin 2) |
| PCB | 100 × 100 mm, 2-layer, 5 mm corner radius, +5 V pour on F.Cu, GND pour on B.Cu, 0.15 mm signal tracks (0.3 mm for some power) |

---

## 2. Block diagram

```
   stack bus: A0–A7, D0–D7, IORQ RD WR M1, RSTB
        │
   A0–A7, IORQB, RDB, WRB ─► PLD IC7 ─┬─► VDPRD (IN 01/02)  ─► VDP /CSR
                                      ├─► VDPWR (OUT 01/02) ─► VDP /CSW      A1 ─► VDP MODE
                                      ├─► OUT6 (OUT 06, ↑ at /WR fall) ─► IC9 74HC574 CP
                                      ├─► IN3  (IN 03) ─► D1 ─► SN76489 /CE
                                      └─► OUT0 (OUT 00, active high) ─► SPEC pin 7 (MTX page latch)

  D0–D7 ─► VDP CD7…CD0 (bit order reversed, TI numbering)
  D0–D7 ─► IC9 sound latch ─► D'0–D'7 ─► SN76489

  ┌──────────── TMS9929A IC1 ────────────┐   Y1 10.7386 MHz, C1/C2 33 pF
  │ AD0–AD7 ─┬─► IC3 574 (CP = ROW = /RAS inverted)       ─► A'0–A'6  ┐
  │          ├─► IC4 574 (CP = COL = /CAS, 3 × HC14 delay) ─► A'7–A'13 ├─► HM62256 IC5 (A14 = GND)
  │          └─► IC2 574 (CP = VWR, /OE = R/W) ─► VD0–VD7 ─┐          ┘   /CS = CAS, /WE = R/W, /OE = VWR
  │ RD0–RD7 ◄──────────────────────────────────── VD0–VD7 ◄┴─► SRAM I/O
  │ RAS, CAS, R/W ─► IC6 74HC14
  │ RESET/SYNC ◄─ RSTB          INT ─► VDPINTB (SPEC pin 3) ─► I/O board CTC TRG0
  │ pin 36 ─► J3, pin 38 ─► J2, pin 35 ─► J4  (470 R to GND each; use depends on chip)
  └──────────────────────────────────────┘

  XT1 4 MHz ─┬─► SN76489 CLK
             └─► bus 4M (SPEC pin 6)
  SN76489 AUDIO ─► C3 100 nF ─► J1 AUDIO
  SN76489 /CE ◄─ D1 ◄─ IN3,  /CE ─► D2 ─► READY + /WE (R5, R1 2k2 pull-ups)
```

---

## 3. Parts (BoM)

| Ref | Part | Function | Datasheet |
|---|---|---|---|
| IC1 | TMS9929A (BoM) or TMS9918A, DIP-40 | VDP: 9929A = PAL component, 9918A = NTSC composite | [TMS9918A/28A/29A Data Manual](https://git.applefritter.com/Apple-1-Tools/apple1-videocard-lib/raw/branch/main/docs/TMS9918A_TMS9928A_TMS9929A_Video_Display_Processors_Data_Manual_Nov82.pdf) |
| IC2 | 74HC574, DIP-20 | VRAM write-data latch, drives the SRAM data bus on writes | [SN74HC574](https://www.ti.com/lit/ds/symlink/sn74hc574.pdf) |
| IC3 | 74HC574, DIP-20 | VRAM row-address latch → A'0–A'6 (silkscreen "LO") | as IC2 |
| IC4 | 74HC574, DIP-20 | VRAM column-address latch → A'7–A'13 (silkscreen "HI") | as IC2 |
| IC5 | HM62256BLP (BoM value reads "HM61256BLP"), 70 ns, DIP-28 | VRAM, 16 K of 32 K used | [HM62256](https://web.mit.edu/6.115/www/document/62256.pdf) |
| IC6 | 74HC14, DIP-14 | Inverts R/W, RAS; 3-stage delay on CAS | [SN74HC14](https://www.ti.com/lit/ds/symlink/sn74hc14.pdf) |
| IC7 | GAL16V8, DIP-20 | I/O decode PLD | [ATF16V8B (compatible)](http://ww1.microchip.com/downloads/en/devicedoc/atmel-0364-pld-atf16v8b-8bq-8bql-datasheet.pdf) |
| IC8 | SN76489(AN), DIP-16 | Sound generator | [SN76489AN manual](http://www.vgmpf.com/Wiki/images/7/78/SN76489AN_-_Manual.pdf) |
| IC9 | 74HC574, DIP-20 | Sound data latch (port 06h) | as IC2 |
| XT1 | 4 MHz full-can DIP-14 oscillator | Sound clock and bus `4M` | [Typical DIP-14 oscillator](http://cdn-reichelt.de/documents/datenblatt/B400/OSZI.pdf) |
| Y1 | 10.7386 MHz crystal, HC-49/U | VDP clock (silkscreen value; BoM says 10.7 MHz) | — |
| C1, C2 | 33 pF disc | Y1 load caps | — |
| D1, D2 | 1N4148, SOD-123 | Sound strobe steering (section 4.5) | [1N4148W](https://www.vishay.com/docs/85748/1n4148w.pdf) |
| R5, R1 | 2k2 | Pull-ups: SN76489 /CE; READY + /WE | — |
| R2, R3, R4 | 470 R | Loads on R-Y, Y, B-Y | — |
| C3 | 100 nF 1206 | Audio coupling | — |
| C4–C8 | 1 µF 1206 | +5 V bypass (the only bypass caps) | — |
| J1–J4 | RCA sockets (custom footprint), left edge | AUDIO, R-Y, Y, B-Y | — |
| JA1–JA4, JA11–JA44 | 8-way "11 mm" stacking sockets (bottom side) | Stack bus (section 6) | — |

---

## 4. Subsystems

### 4.1 VDP CPU interface (IC1)
- `/CSR` = PLD `VDPRD` (IN 01h or 02h), `/CSW` = PLD `VDPWR` (OUT 01h or 02h), `MODE` = **A1**.
  - Port `01h`: MODE = 0 → VRAM data.
  - Port `02h`: MODE = 1 → register write / address set-up (write), status (read).
  - These are the MTX512 VDP ports.
- Data bus: TI numbers CD0 as the MSB, so bus D0 → CD7 (pin 17) … bus D7 → CD0 (pin 24). Correct.
- `RESET/SYNC` (pin 34) = bus `RSTB`, so the system reset resets the VDP.
- `INT` (pin 16) → `VDPINTB` only. The TMS99xxA's INT is a push-pull output (not open-drain), so it needs no pull-up. That answers the I/O board document's open question. It also means nothing else may drive `VDPINTB`.
- `GROMCLK` (pin 37) is not connected.
- No `/WAIT` on the bus, so software must pace VRAM accesses itself (minimum spacing between data-port accesses depends on the display mode; see the data manual).

### 4.2 Static VRAM (IC2–IC6)
The TMS9929A expects 4116 DRAMs: a multiplexed address on AD0–AD7 with RAS/CAS, a separate read-data bus RD0–RD7, and write data put back onto AD0–AD7 late in the cycle. This board emulates that with latches and one 32 K SRAM.

- **Row latch IC3:** `CP` = `ROW` = RAS inverted (IC6 5→6), so it latches on RAS falling. Takes AD1–AD7 → A'0–A'6.
- **Column latch IC4:** `CP` = `COL` = CAS through three Schmitt inverters (IC6 9→8→11→10→13→12), so it latches on CAS falling plus three gate delays. Takes AD1–AD7 → A'7–A'13. Schematic note "TIMING DELAYS", silkscreen "TIMING ADJUSTMENT".
  - **Why the delay (designer):** the VDP's sequencing assumes 4116 DRAM, which latches its column address internally a little after CAS falls. The VDP's AD timing around CAS edges is built around that behaviour. With an SRAM and an edge-triggered '574 there is no such internal latch, so the delay has to be added artificially to put the latch edge where the column address is valid on AD1–AD7.
  - The delay depends on the HC14 actually fitted (family, manufacturer, temperature). A 74HCT14 (observation 1) has a different propagation delay to a 74HC14, so recheck the latch edge on the scope after any change of part.
- AD0 is used by neither latch. In 16 K (4116) mode the VDP puts its 7-bit row and column on AD1–AD7. **Software must set the 4/16K bit** (R1 bit 7, TI's bit 0). In 4 K mode the address bits come out differently and VRAM would alias.
- Q0 of IC3 and IC4 is not connected. SRAM A14 is tied to GND, so only 16 KB of the 32 KB is used. (The silkscreen "8kB STATIC VRAM" is wrong.) Row and column bits land on the SRAM in a permuted order. That doesn't matter, because the VDP is the only thing that addresses it.
- **SRAM IC5:** `/CS` = CAS (directly), `/WE` = R/W, `/OE` = `VWR` (R/W inverted by IC6 1→2). Refresh cycles are RAS-only, so the SRAM isn't selected during them.
- **Read:** R/W high → SRAM `/OE` low, IC2 outputs off. SRAM drives VD0–VD7 = VDP RD0–RD7.
- **Write:** R/W low → IC2 latches AD0–AD7 on `VWR` rising (R/W falling plus one gate) and drives VD0–VD7 (`/OE` = R/W). SRAM `/OE` goes high and the write happens while CAS and R/W are both low.
- IC6 pin 4 (`VRD`) is an unused output.

### 4.3 Video outputs
The socket for IC1 takes either family member, and the designer has boards built both ways. Pins 35, 36 and 38 change function with the chip:

| VDP pin | Net / socket | TMS9929A (component, PAL 50 Hz) | TMS9918A (composite, NTSC 60 Hz) |
|---|---|---|---|
| 36 | `Y` → J3 | Y (luma + sync) | **COMVID**, composite colour video |
| 38 | `R-Y` → J2 | R-Y | **CPUCLK** output (XTAL/3 ≈ 3.58 MHz) |
| 35 | `B-Y` → J4 | B-Y | **EXTVID** input (external video, for a second VDP) |

- Each of the three has a 470 R load to GND and nothing else: no buffer, no 75 Ω source matching, no coupling caps.
- **In use:** there is no component display, so the picture is always taken from J3.
  - **TMS9918A fitted:** J3 is real composite colour video. J2 carries the CPU clock, loaded by R2, and isn't a video signal. J4 is the EXTVID input, held at GND by R4, which is its normal idle state.
  - **TMS9929A fitted:** J3 is Y, luma with sync. A composite monitor accepts it as a **monochrome** picture; J2 and J4 carry the colour information, which is unused.
- The chip also sets the frame rate: 50 Hz with the 9929A, 60 Hz with the 9918A. The VDP interrupt rate follows, so software that times itself on frame interrupts runs 20 % faster with the 9918A. Original MTX software assumes 50 Hz.
- The 10.7386 MHz crystal suits both chips.
- Silkscreen near C1/C2 reads "VDP SYNC TRIMMERS", but both are fixed 33 pF parts.

### 4.4 Clock (XT1)
- 4 MHz DIP-14 can, `EN` (pin 1) unconnected. Output → SN76489 `CLK` **and** bus `4M` (SPEC pin 6).
- This board is the **driver of the bus `4M` line** (open question in the overview). Consumers so far: Z80 SBC JJP1 (when linked 1–2, it runs the CPU from this oscillator) and I/O board JP2 (baud-master option).
- With the Z80 SBC set to take `4M`, its 330 R CLK pull-up (R18) and the CLK load of the whole stack hang on this oscillator.

### 4.5 Sound (IC8, IC9, D1, D2)
- **Data:** `OUT (06h)` → PLD `OUT6`, active high, which rises when `/WR` falls. IC9 latches D0–D7 on that edge. This relies on write data being valid **before** `/WR` falls. The Z80 does that (data is out from T1, `/WR` falls in T2). `/OE` of IC9 is tied low.
- Bit order: the SN76489's TI pin names call pin 3 "D0" (MSB) and pin 10 "D7" (LSB). The KiCad symbol uses LSB-first names instead. Bus D0 → pin 10 (LSB) … bus D7 → pin 3 (MSB), which is correct.
- **Strobe:** `IN (03h)` → PLD `IN3` low. The returned byte is whatever is on the bus (no device drives it; `FFh` with the Z80 SBC's pull-ups).
- **Self-timed write:**
  1. `IN3` low pulls `/CE` low through D1 (R5 pulls it up otherwise).
  2. With `/CE` low the SN76489 pulls its open-collector READY low, even with `/WE` high. READY is tied to `/WE` (R1 pull-up), so `/WE` goes low and the chip takes the data.
  3. While READY is low, D2 holds `/CE` low, so the cycle completes after `IN3` has gone away.
  4. After about 32 clocks (**8 µs** at 4 MHz) READY releases; R1 and R5 pull `/WE` and `/CE` high.
- Consequence for software: leave at least 8 µs after `IN (03h)` before the next `OUT (06h)`, or the chip may take the new byte instead.
- The SN76489 has no reset pin. It powers up with random tones until software silences it, and `RSTB` doesn't help.
- Tone frequency = 4 MHz / (32 × N), N = 10-bit divider.
- **Audio:** `AUDIO` → C3 (100 nF) → J1. No load resistor on either side.

### 4.6 Power
- +5 V only, from SPEC pin 2. No regulator.
- Bypass: C4–C8 (1 µF) for 9 ICs plus the oscillator.
- Copper: +5 V pour on F.Cu, GND pour on B.Cu.

---

## 5. I/O map (from the PLD)

| Port | Read | Write | Device |
|---|---|---|---|
| `00h` | — | `OUT0` pulse (active high) → SPEC pin 7 | MTX board page latch |
| `01h` | VRAM data | VRAM data | VDP (MODE 0) |
| `02h` | Status | Register / address set-up | VDP (MODE 1) |
| `03h` | Sound strobe (data undriven) | — | SN76489 |
| `06h` | — | Sound data latch | IC9 |

- Full 8-bit decode (A0–A7), no mirrors in `00–FF`. A8–A15 not decoded.
- No clash with the I/O board: it **reads** `06h` (`IN6`, keyboard) and this board only **writes** it. No clash with the Z80 SBC (`18h`, `20h`).
- `OUT0` pulses on any `OUT (00h)`, in every configuration. Harmless without the MTX board.

---

## 6. Connectors

### 6.1 Stack bus
One footprint per group, bottom side, same corner layout as the other boards. Every group passes through.

| Corner | Connectors |
|---|---|
| Top-left | JA1 ADDR, JA11 ADDR2 |
| Top-right | JA2 SPEC, JA22 PROG |
| Bottom-left | JA4 DATA, JA44 AUX |
| Bottom-right | JA3 CTRL, JA33 MTX |

| Conn | Name | Pins 1→8 | Use on this board |
|---|---|---|---|
| JA1 | ADDR | A0 … A7 | A0–A7 → PLD; A1 → VDP MODE |
| JA11 | ADDR2 | A15 … A8 (reversed) | Pass-through |
| JA4 | DATA | D0 … D7 | VDP (reversed), IC9 |
| JA3 | CTRL | RSTB, CLK, M1B, MREQB, IORQB, RDB, WRB, INTB | RSTB → VDP reset. M1B → PLD (unused in equations). IORQB, RDB, WRB → PLD. CLK, MREQB, INTB pass-through |
| JA2 | SPEC | GND, +5V, VDPINTB, IEO1, IEO2, 4M, OUT0, KBDRST | +5 V **in**. VDPINTB **driven** by VDP INT. 4M **driven** by XT1. OUT0 **driven** by PLD. KBDRST → PLD pin 13 (input, unused). IEO1, IEO2 pass-through |
| JA22 | PROG | SP3, ROM7, BUSRQ, ROMWEX, ROMCSX, RESX, ROMOEX, PWR | Pass-through only (PWR carries 12 V from the CPU board) |
| JA33 | MTX | P0 P1 P2 P3 R0 R1 R2 CPM | Pass-through |
| JA44 | AUX | AUX1 … AUX8 | Pass-through |

### 6.2 RCA sockets (left edge, top to bottom)
| Ref | Silkscreen | Signal |
|---|---|---|
| J1 | AUDIO | SN76489 via C3 100 nF |
| J4 | B-Y | VDP pin 35: B-Y (9929A) / EXTVID input (9918A); 470 R to GND |
| J3 | Y | VDP pin 36: Y (9929A, used as mono composite) / composite colour (9918A); 470 R to GND |
| J2 | R-Y | VDP pin 38: R-Y (9929A) / CPUCLK (9918A); 470 R to GND |

Sleeves are all GND. There are no other headers or jumpers.

---

## 7. PLD (IC7, GAL16V8) — pin use

All 18 signal pins are connected. Pin 13 is configured as an input with no equation, so it is the only free pin.

| Pin | Signal | Dir | Notes |
|---|---|---|---|
| 1 | IORQB | in | |
| 2 | M1B | in | Declared, not used |
| 3–9, 11 | A0–A7 | in | `FIELD ADDR = [A7..A0]` |
| 12 | OUT0 | out, **active high** | SPEC pin 7 |
| 13 | KBDRST | in (not in the source) | SPEC pin 8; output disabled in the fuse map |
| 14 | IN3 | out | → D1 → SN76489 /CE |
| 15 | VDPWR | out | VDP /CSW |
| 16 | VDPRD | out | VDP /CSR |
| 17 | OUT6 | out, **active high** | IC9 CP |
| 18 | RDB | in (I/O pin used as input) | |
| 19 | WRB | in (I/O pin used as input) | |

Equations (WinCUPL, `Device g16v8a`; the `.jed` is simple mode, `g16v8as`):
```
 OUT6  = ADDR:6 & !IORQB & !WRB ;                               /* OUT 06h, rising edge latches */
!IN3   = ADDR:3 & !IORQB & !RDB ;                               /* IN  03h                     */
!VDPRD = ADDR:2 & !IORQB & !RDB  #  ADDR:1 & !IORQB & !RDB ;    /* IN  01h/02h                 */
!VDPWR = ADDR:2 & !IORQB & !WRB  #  ADDR:1 & !IORQB & !WRB ;    /* OUT 01h/02h                 */
 OUT0  = ADDR:0 & !IORQB & !WRB ;                               /* OUT 00h, MTX page latch     */
```
- The fuse map (`.jed`, built 2023-07-26, name `z80-VDP-out0`) was decoded term by term: one product term each for OUT6, IN3, OUT0, two each for VDPRD and VDPWR, all matching the source. XOR bits make OUT6 and OUT0 active high and the rest active low. AC1 bits set pins 13, 18 and 19 as inputs. Simple mode (SYN = 1, AC0 = 0). The `.PLD` `Date` field says 12/1/2023, but the logic is the same.
- Every select is gated by `/RD` or `/WR`, so an interrupt-acknowledge cycle (`/M1` + `/IORQ`, no strobe) can't trigger any of them.
- `/MREQ` isn't needed (I/O only).

---

## 8. Timing notes

- **Decode:** GAL16V8 delay (speed grade not recorded, typically 10–25 ns). Z80 I/O cycles include an automatic wait state, so this is comfortable at 4 MHz.
- **Sound latch** clocks on the **leading** edge of `/WR` (section 4.5). Fine on the Z80. On the 6502 SBC it depends on how its PLD makes `WRB`: a 6502 puts write data on the bus only partway through φ2, so if `WRB` falls at φ2 rise the latch could catch stale data.
- **VRAM, column latch:** the SRAM's `/CS` is CAS directly, but its upper address comes from IC4, which updates three HC14 delays (very roughly 35–75 ns) after CAS falls. For that window the SRAM sees the previous column address with `/CS` low.
  - Reads: harmless. Data is valid about one HC574 delay plus 70 ns after the latch updates.
  - Writes: safe only as long as R/W falls after IC4 has updated. The board works, so it does, but the margin isn't documented.
  - Worth one scope capture of CAS, COL, R/W and VWR.
- **VRAM write start:** when R/W falls, IC2 starts driving at once, but the SRAM's `/OE` only goes high one HC14 delay later. If the SRAM was already selected (CAS low), both drive VD0–VD7 for about 10–25 ns on every write.
- **Write data setup:** IC2 latches AD0–AD7 one HC14 delay after R/W falls. This assumes the VDP's write data is already on AD at that point. *To confirm on the scope with the above.*
- **Sound write:** about 8 µs per byte (32 × 250 ns), not held off by hardware.

---

## 9. Observations for the next revision

Most important first.

1. **HC inputs driven by NMOS outputs.** IC2–IC4 and IC6 take AD0–AD7, RAS, CAS and R/W straight from the TMS9929A, an NMOS part rated for V<sub>OH</sub> ≥ 2.4 V. 74HC inputs need about 3.15–3.5 V at 5 V. It works because the lightly loaded NMOS outputs rise well above their minimum, but it's out of spec. Fit **74HCT574 / 74HCT14**. (The schematic symbol is already the 74HCT574.)
2. **Sound strobe diode levels.** `/CE` is pulled low through a 1N4148 (D1, or D2 + READY's V<sub>OL</sub>): roughly 0.7–1.1 V, at or above the SN76489's 0.8 V V<sub>IL</sub> limit. It works because the NMOS threshold is typically nearer 1.4 V. Schottky diodes (e.g. BAT54) would give about 0.3 V of margin.
3. **VRAM timing margins undocumented** (section 8): the stale column address at the start of a CAS cycle and the brief contention at the start of each write. A cleaner scheme: gate SRAM `/CS` with the delayed `COL` instead of CAS, and drive IC2's `/OE` from a signal that only goes active after the SRAM's `/OE` is off. Check with the scope before changing anything.
4. **Audio coupling.** 100 nF into a typical 10 k amplifier input is a high-pass at about 160 Hz, which cuts most of the bass. Use 1–10 µF, and add a load resistor to GND on the chip side (around 1 k) to bias the output and fix the DC level.
5. **Video outputs unbuffered and not matched.** The 470 R loads are the only conditioning. A 75 Ω input on the display pulls the levels down and puts the cable on the VDP pins. Add an emitter-follower or video op-amp buffer with 75 Ω series resistors.
   - With a TMS9929A the only usable output is monochrome. A PAL encoder (as on the original MTX) or a Y/R-Y/B-Y → RGB matrix would give colour from the 9929A, and keep the 50 Hz timing that MTX software expects.
   - With a TMS9918A, R2 loads the CPUCLK output (3.58 MHz into 470 R) and the clock appears on J2. Harmless, but a jumper or a fit-per-chip option for R2/R4 would be tidier. Label the sockets for both chips.
6. **Floating bus when the programmer holds it.** While `BUSRQ` is active, `/IORQ`, `/RD`, `/WR` float (project-wide issue, Z80 SBC item 2), and the programmer drives low ROM addresses such as `01h`, `02h`, `06h`. This PLD could then write garbage into VDP registers or VRAM, start a sound write or pulse `OUT0`. The target is reset afterwards, which resets the VDP registers but not VRAM or the SN76489.
7. **Sound chip has no reset.** It powers up making noise. A hardware mute on reset (e.g. hold the audio path muted while `RSTB` is low) or early silencing in every ROM.
8. **Almost no decoupling.** Five 1 µF caps for nine ICs plus a 4 MHz oscillator and a 10.7 MHz crystal oscillator. Add 100 nF at each IC, especially the VDP, SRAM and the latches that switch at the VRAM rate.
9. **`4M` driven from this board.** The Z80 SBC can run its CPU from it, so the CPU board's clock then depends on which optional board is fitted, and the oscillator drives the whole stack's CLK load (plus the Z80 SBC's 330 R pull-up). Either keep the CPU clock on the CPU board, or buffer `4M` here (e.g. a 74HC/AC gate per load).
10. **VDP `INT` is push-pull.** No pull-up is needed, but nothing else may share `VDPINTB`. Leave it point-to-point. If a later board wants to share it, add an open-collector buffer.
11. **Spare PLD pin 13** sees `KBDRST` as an input. Fine as is. If the line has no purpose here, removing the connection frees the pin.
12. **Housekeeping:**
    - Silkscreen "8kB STATIC VRAM" should read 16 KB (of 32 KB); "VDP SYNC TRIMMERS" refers to trimmers that aren't fitted (C1/C2 are fixed 33 pF).
    - IC5's BoM value reads "HM61256BLP" (the part is an HM62256BLP). Y1's BoM value is 10.7 MHz; the silkscreen has the exact 10.7386 MHz.
    - The PCB print `V102-VDP-1.pdf` title block reads "NOVA Z80 v101 – VDP & SOUND Board", dated 2022-09-29.
    - The folder holds `PHONO-SRC-00A-erc.rpt` (name from another project), an extension-less file `V102-VDP-1` (an old 2023 BoM CSV), `V102-VDP-1.kicad_sch-bak` and an empty `cd4530cf-….log`.
    - The GAL16V8 speed grade isn't recorded. The PLD source's `Company` field is `xxx`.

---

## 10. Open questions

- What the audio output drives (input impedance, so the real low-frequency cut-off is known).
- Whether the three-gate CAS delay was set by measurement, and the delay/edge position actually achieved (scope: CAS, COL, AD1–AD7).
- Whether anything should drive `4M` in the MTX configuration besides this board (confirm when the MTX board is documented).
- How the 6502 SBC's PLD generates `WRB` relative to valid write data (sound latch, section 8).
- Why `KBDRST` reaches PLD pin 13 (revision note "reconfigured off-board pins").
