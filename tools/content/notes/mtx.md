# NOVAZ80 MTX Board — V102-MTX-2 (Rev 001)

Design analysis from `V102-MTX-2.net` (KiCad/Eeschema 9.0.7 export, 2026-11-25), the schematic (single sheet, `V102-MTX-2.kicad_sch`), the BoM and the PCB file (`V102-MTX-2.kicad_pcb`). ERC: 0 errors / 0 warnings. DRC: 0 violations, 0 unconnected pads, 0 footprint errors.

Title block: *NOVAZ80 MTX – V102 MTX Board*, Nova Embedded Solutions, dated 2024-01-02, Rev 001.
Revision note: "Added control of ROM.A13 from PLD for programming to make use of 3rd 8kB block in RAM [sic: ROM] A|B|x|C".

PLD: `v102-mtx-2.PLD` and `v102-mtx-2.jed`. The fuse map was decoded and matches the source equations (section 7). Earlier versions `v102-mtx-0` and `v102-mtx-1` are in the same folder (history in section 7.3).

---

## 0. Where this board sits in the NOVAZ80 project

The CPU board for the **Memotech MTX512** configuration. It is a Z80 with the MTX's paged ROM/RAM memory system and nothing else:

- **Z80 CPU**, clocked from the bus (no oscillator on this board),
- **32 K main ROM** (28C256) holding the MTX ROMs A, B and C plus one spare 8 K block,
- an optional **second 28C256 ("ROMx")** for extension code,
- **64 K RAM** in two 62256s ("MTX500" 32 K + "MTX512" 32 K),
- the **page register** (74AHC273, the MTX `RELCPMH` register at port `00h`) and an ATF20V8B PLD that turns it into chip selects.

It has **no I/O devices and no I/O decode of its own**. Everything at I/O addresses comes from other boards:

| Needs | From |
|---|---|
| CPU clock (`4M` / `CLK`) | VDP + sound board (V102-VDP-1) oscillator |
| `OUT0` strobe for the page register | VDP + sound board PLD |
| VDP, sound | VDP + sound board |
| CTC (incl. VDP interrupt), keyboard, serial | I/O board (V102-IO1-0) |

So the **I/O and VDP/sound boards are both required** in this configuration; without the VDP board the CPU has no clock.

Like the Z80 SBC, this board is the **+5 V source for the stack** (DC-DC module onto SPEC pin 2). Only one CPU board is fitted in a stack.

Status: built, tested and in use. Section 9 collects observations for the planned 4-layer revision.

---

## 1. Summary

| Item | Value |
|---|---|
| CPU | Z80, CMOS (silkscreen "Z80 CMOS CPU"), DIP-40 |
| Main ROM | 28C256, 32 K = four 8 K blocks A \| B \| n \| C (silkscreen "ROMABC 4x8kB: A\|B\|n\|C") |
| Expansion ROM | ROMx: optional 28C256 ("28C256 ONLY"), enable jumper J3, address jumpers J2/J4 |
| RAM | 2 × HM62256 = 64 K ("RAM 32kB – MTX500", "RAM2 32kB – (MTX512)", RAM2 marked optional) |
| Paging | 74AHC273 page register (`OUT (00h)`, clocked by the VDP board's `OUT0`), cleared by reset |
| Glue | ATF20V8B PLD: memory selects and ROM A13/A14 only (no I/O decode, no `/IORQ`) |
| Reset | MAX811L (4.63 V) + reset button + bus `KBDRST`; programmer `RESX` merged by a 74LVC2G02 |
| Clock | **None on board.** `CLK` is tied to bus `4M` (from the VDP board, 4 MHz) |
| Interrupts | `/INT` from the bus only (1 k pull-up). No daisy-chain parts on this board |
| Power | DC jack (silkscreen "DC IN 7.5V–15V") → push-button DPDT switch → buck module → +5 V |
| PCB | 100 × 100 mm, 2-layer, +5 V pour on F.Cu, GND pour on B.Cu, 0.15 mm signal tracks (0.4 mm power) |

---

## 2. Block diagram

```
 Barrel jack PL1 ─PWR─┬──────────────────────────────────► PROG pin 8 (raw input, unswitched)
          sleeve GND1 │
                      └─ SW2 (DPDT) ─PWR1/GND2─► PW1 DC-DC ─► +5V ─► SPEC pin 2 (feeds the stack)
                                                              └─R3─► D2 power LED

 SPEC 4M ═══ CTRL CLK ═══► CPU CLK            (one net on this board; R5 470R pull-up)

 SW1 RESET ┐
 SPEC KBDRST┴─► MAX811 /MR ─► RESB ─► IC9a NOR (inverter) ─┐
 PROG RESX ────────────────────────────────────────► IC9b NOR ─► RSTB ─► CPU /RESET, 273 /MR, CTRL pin 1

 SPEC OUT0 ─► 74AHC273 CP      D0–D7 ─► 273 ─► P0–P3, R0–R2, CPM ─► MTX group (bus) and PLD

 A13 A14 A15 MREQB, P0–P3, R0–R2, CPM, ROMCSX, SELECT (SW3)
        │
        ▼
     PLD IC6 ─┬─► ROM    ─► main ROM /CS        ROMA13, ROMA14 ─► main ROM A13, A14
              ├─► ROMX ─J3─► ROMx /CS (R10 pull-up)
              ├─► RAM    ─► RAM  /CS (MTX500)
              ├─► RAM2   ─► RAM2 /CS (MTX512)
              └─► ROM7   ─► PROG pin 2 (off-board cartridge ROM 7)

 Main ROM, ROMx:  A0–A12 from CPU,  /OE = ROMOEX (1k pull-down),  /WE = ROMWEX (1k pull-up)
 ROMx A13/A14:    CPU A13/A14 via jumpers J4/J2, else 1k to GND
 RAM, RAM2:       A0–A14 from CPU,  /OE = GND,  /WE = WRB

 ┌──────────┐  A0–A15, D0–D7 (4k7 pull-DOWNs), M1 MREQ IORQ RD WR INT BUSRQ ─► stack (no buffers)
 │ Z80 CPU  │  NMI, WAIT: tied straight to +5V.  HALT, RFSH, BUSACK: not connected.
 └──────────┘
```

---

## 3. Parts (BoM)

| Ref | Part | Function | Datasheet |
|---|---|---|---|
| IC1 | Z80 CPU (CMOS, Z84C00 family), DIP-40 | CPU | [Z84C00](http://www.zilog.com/docs/z80/ps0178.pdf), [Z80 User Manual UM0080](http://www.zilog.com/docs/z80/um0080.pdf) |
| IC2 | 28C256, DIP-28 (600 mil), BoM value "ROM" | Main ROM: MTX ROMs A, B, C + spare block | [AT28C256](https://ww1.microchip.com/downloads/en/DeviceDoc/doc0006.pdf) |
| IC5 | 28C256, DIP-28 (600 mil), BoM value "ROMX" | Optional expansion ROM ("ROMx") | as IC2 |
| IC3 | HM62256BLP, DIP-28 (300 mil), BoM value "RAM" | RAM, 32 K ("MTX500") | [HM62256](https://web.mit.edu/6.115/www/document/62256.pdf) |
| IC4 | HM62256BLP, DIP-28 (300 mil), BoM value "RAM2" | RAM, 32 K ("MTX512", optional) | as IC3 |
| IC6 | ATF20V8B (symbol ATF20V8B-10PU), DIP-24 | Memory decode PLD | [ATF20V8B](https://pages.uoregon.edu/torrence/432/spec/ATF20V8.pdf) |
| IC7 | 74AHC273, DIP-20 | Page register (MTX `RELCPMH`, port 00h) | [74AHC273](https://assets.nexperia.com/documents/data-sheet/74AHC_AHCT273.pdf) |
| IC8 | MAX811LEUS-T, SOT-143 | Reset supervisor, 4.63 V, manual-reset input | [MAX811](https://www.analog.com/media/en/technical-documentation/data-sheets/MAX811-MAX812.pdf) |
| IC9 | 74LVC2G02, VSSOP-8 | Dual NOR: reset merge (MAX811 + programmer `RESX`) | [SN74LVC2G02](https://www.ti.com/lit/ds/symlink/sn74lvc2g02.pdf) |
| PW1 | Buck module, 4-pin (GND, Vout, Vin, GND), footprint `dc_dc_1` | +5 V for the board and the stack | Generic module, no datasheet |
| PL1 | Barrel jack with switch, Würth 6941xx301002 | Power input | [Würth 694106301002](https://www.we-online.com/components/products/datasheet/694106301002.pdf) |
| SW2 | DPDT push switch, right-angle | Power on/off | — |
| SW1 | Tactile switch, right-angle (PTS645) | Reset | — |
| SW3 | SPDT slide switch | "PROG TARGET": main ROM or ROMx | — |
| J3 | 1×2 header (jumper), silkscreen "EN/DIS" | ROMx enable | — |
| J2, J4 | 1×2 headers (jumpers), silkscreen "-A14-", "-A13-" | ROMx A14 / A13 from CPU, or grounded | — |
| J1 | 1×1 pin, silkscreen "GND" | Ground test point | — |
| JA1–JA8 | 8-way "11 mm" stacking sockets (bottom side) | Stack bus (section 6) | — |
| C1, C3–C8 | 100 nF 1206 | Bypass | — |
| C2 | 1 µF 1206 | +5 V bulk | — |
| D2 / R3 | LED / 470 R | Power indicator | — |
| R5 | 470 R | CLK pull-up | — |
| RN1, RN2 | 4k7 × 4 arrays | D0–D7 **pull-downs** (schematic note "DATA BUS PULL-DOWNS") | — |
| R1, R4, R7, R9, R10 | 1 k | Pull-ups: KBDRST, INTB, ROMWEX, BUSRQ, ROMx /CS | — |
| R2, R6, R8, R12 | 1 k | Pull-downs: RESX, ROMx A14, ROMx A13, ROMOEX | — |

There is no CTC, PIO or oscillator on this board, and no pull-up on `IEO1` (compare the Z80 SBC).

---

## 4. Subsystems

### 4.1 CPU (IC1)
- Address and data buses go straight to the memories and the stack. **No bus buffers.**
- `/NMI` and `/WAIT` are **tied directly to +5 V** (no resistor). `/HALT`, `/RFSH`, `/BUSACK` are not connected.
- `/BUSRQ`: 1 k pull-up (R9), on PROG pin 3 for the programmer.
- `/INT`: from CTRL pin 8 only, 1 k pull-up (R4). The interrupt sources are the I/O board's CTC/SIO/PIO.
- `/IORQ`, `/M1`, `/RD` go only to the bus. `/WR` also drives both RAM `/WE` pins. Only `/MREQ` reaches the PLD.
- **D0–D7 have 4k7 pull-downs**, not pull-ups as on the Z80 SBC. Unmapped memory and undriven I/O ports read `00h` on this board.

### 4.2 Clock
- The CPU `CLK` pin, CTRL pin 2 (`CLK`) and SPEC pin 6 (`4M`) are **one net**. There is no oscillator and no jumper.
- The clock comes from the VDP board's 4 MHz can (V102-VDP-1 section 4.4), which therefore drives the CPU and the whole stack's `CLK` line, the same frequency as a real MTX.
- R5 (470 R) pulls `CLK` up to +5 V, about 10 mA in each low half-cycle (same idea as the Z80 SBC's 330 R).
- On this configuration, the I/O board's JP2 "bus 4M" option is the CPU clock itself.

### 4.3 Reset
- **MAX811L (IC8):** holds `RESB` low for at least 140 ms after +5 V rises above about 4.63 V. Its `/MR` is pulled low by **SW1** or the bus line **`KBDRST`** (MTX keyboard reset key via the I/O board's J6). R1 is an extra 1 k pull-up on `/MR`.
- **IC9 (74LVC2G02)**, two NOR gates, replaces the PLD reset term used on the Z80 SBC:
  - Gate 1: both inputs = `RESB` → output = NOT `RESB`.
  - Gate 2: inputs = NOT `RESB` and `RESX` (PROG pin 6, 1 k pull-down R2) → output = **`RSTB`**.
  - `RSTB` is low when `RESB` is low **or** `RESX` is high (same function as the Z80 SBC).
- `RSTB` drives the CPU `/RESET`, CTRL pin 1 (system reset for the stack) and the **74AHC273 `/MR`**. Reset therefore clears the page register: ROM mode, ROM page 0, RAM page 0, as on a real MTX after reset.

### 4.4 Page register (IC7, 74AHC273) — MTX `RELCPMH`
- D0–D7 from the data bus. `CP` = bus `OUT0` (SPEC pin 7), which the VDP board's PLD drives high during `OUT (00h)` while `/WR` is low. The '273 latches on the rising edge, i.e. as `/WR` falls (plus the VDP PLD delay). The Z80 has write data on the bus from T1, so it's valid by then.
- Outputs go to the MTX bus group **and** to the PLD:

| Bit | 273 output | Signal | MTX meaning |
|---|---|---|---|
| D0–D3 | Q0–Q3 | `P0`–`P3` | RAM page |
| D4–D6 | Q4–Q6 | `R0`–`R2` | ROM page (2000–3FFF) |
| D7 | Q7 | `CPM` | 0 = ROM mode, 1 = all-RAM (CP/M) mode |

- **Write-only** (as on the MTX). Software must keep its own copy of the last value written.
- The MTX group (JA8) carries the register to the rest of the stack for any board that wants to follow the paging. None of the documented boards uses it yet.

### 4.5 Main ROM (IC2) — A | B | n | C
- A0–A12 from the CPU. **A13 = PLD `ROMA13`, A14 = PLD `ROMA14`**, so the PLD chooses which 8 K block of the chip appears at 2000–3FFF.
- `/CS` = PLD `ROM`. `/OE` = `ROMOEX` (PROG pin 7, 1 k pull-down → **always enabled** unless the programmer pulls it high). `/WE` = `ROMWEX` (PROG pin 4, 1 k pull-up → **the Z80 can't write the ROM**).
- Chip layout and CPU mapping (ROM mode, section 5):

| Chip address | Block | Content | CPU address | Selected when |
|---|---|---|---|---|
| `0000–1FFF` | A | MTX OS ROM | `0000–1FFF` | always (ROM mode) |
| `2000–3FFF` | B | MTX ROM page 0 (BASIC) | `2000–3FFF` | R = 0 |
| `4000–5FFF` | n | spare 8 K "embedded" user ROM | `2000–3FFF` | R = 3 |
| `6000–7FFF` | C | MTX ROM page 1 | `2000–3FFF` | R = 1 |

- When programming (`ROMCSX` high) the PLD makes `ROMA13`/`ROMA14` follow the bus A13/A14, so the whole 32 K chip is programmed as one flat image in the order above.

### 4.6 Expansion ROM ("ROMx", IC5) — optional
- A0–A12 from the CPU. `/OE`, `/WE` shared with the main ROM (`ROMOEX`, `ROMWEX`).
- **A13 / A14** come through jumpers **J4 ("-A13-")** and **J2 ("-A14-")** from the CPU's A13/A14. With a jumper removed, R8/R6 (1 k) hold that pin low (schematic: "ROM EARTH JUMPERS").
- **`/CS`** comes from PLD `ROMX` through **J3 ("EN/DIS")**. With J3 removed, R10 holds `/CS` high and ROMx is disabled.
- The PLD selects ROMx for **`2000–7FFF` when R = 6** (ROM mode). With J2 and J4 fitted that's chip `2000–7FFF` (24 K; chip `0000–1FFF` is never reached at run time). With both removed, the same chip block `0000–1FFF` appears three times.
- The PLD drops RAM2 out of `4000–7FFF` (P = 0) while R = 6, so ROMx takes over that 16 K.
- Schematic note: **must be a 28C256**, because the programmer uses page-write mode, which the 8 K part doesn't have. The silkscreen agrees ("OPTIONAL EXPANSION (28C256 ONLY)").
- The silkscreen next to IC5 still reads "ROMx (2000-3FFF R=x)", which is older than the current PLD (section 9, item 8).

### 4.7 RAM (IC3 "RAM", IC4 "RAM2")
- Both take A0–A14 from the CPU directly. `/OE` **tied to GND**, `/WE` = `/WR`, `/CS` from the PLD.
- IC3 is the MTX500's 32 K; IC4 is the extra 32 K of the MTX512 (silkscreen "OPTIONAL EXPANSION"). Without IC4 the board is an MTX500.
- With `/OE` permanently active a selected RAM drives the data bus until `/WR` falls, on every write (same as the Z80 SBC, section 9 item 1).

### 4.8 Off-board ROM 7
- PLD `ROM7` (active low) is driven onto **PROG pin 2** for `2000–3FFF` when R = 7. It's the chip select for an off-board cartridge ROM (PLD comment "select for cartridge rom 7 - off board").
- This answers the overview's question about `ROM7`: it's an **output from the MTX board**. The Z80 SBC and I/O board leave PROG pin 2 unconnected, and on the programmer it's a single-node net.

### 4.9 Programming support
- **SW3 "PROG TARGET"** drives PLD `SELECT`: +5 V = main ROM ("ROM ABC"), GND = ROMx.
- While the programmer holds `ROMCSX` high:
  - `SELECT` = 1 → main ROM `/CS` forced low, `ROMA13`/`ROMA14` = bus A13/A14 (whole chip addressable).
  - `SELECT` = 0 → ROMx `/CS` forced low (if J3 is fitted). ROMx A13/A14 follow the bus only if J4/J2 are fitted.
- `ROMOEX` and `ROMWEX` go to both ROMs; only the selected one responds.
- **`ROMCSX` has no pull-down on this board** (the Z80 SBC has 1 k). See section 9, item 2.
- `RESX` resets the system through IC9 at the end of programming, which also clears the page register.

### 4.10 Power
- PL1 centre pin = `PWR`. It goes **unswitched** to PROG pin 8, as on the Z80 SBC.
- **Ground differs from the Z80 SBC.** The jack's sleeve (`GND1`) is *not* board GND. SW2 pole 2 connects it to PW1 pin 4 (`GND2`), and only PW1 pin 1 is on board GND. So the supply's return reaches the board only through SW2 and the module's internal ground link.
  - With SW2 off, the 12 V on PROG pin 8 has no return path on this board. It's still a hazard if anything else in the stack provides a ground path to the supply (e.g. USB on the I/O board or programmer to a PC that shares ground with the adaptor).
  - With SW2 on, the full supply current returns through PW1's ground. This works on the built board, so the module's two GND pads are common.
- SW2 pole 1 switches `PWR` → `PWR1` (PW1 Vin).
- Silkscreen: "DC IN 7.5V–15V". The module's own input rating isn't recorded (section 10).
- D2 (via R3 470 R) shows +5 V is present.
- Bypass: seven 100 nF plus one 1 µF for nine ICs. Much better than the other v102 boards.
- Copper: +5 V pour on F.Cu, GND pour on B.Cu.

---

## 5. Memory map (from the PLD)

No I/O devices on this board. The only port it uses is `00h` (write), decoded by the VDP board as `OUT0`.

### ROM mode (`CPM` = 0)

| CPU address | P = 0 | P = 1 | P ≥ 2 |
|---|---|---|---|
| `0000–1FFF` | ROM A | ROM A | ROM A |
| `2000–3FFF` | paged ROM (table below) | paged ROM | paged ROM |
| `4000–7FFF` | RAM2 chip `4000–7FFF` (ROMx instead when R = 6) | — | — |
| `8000–BFFF` | RAM chip `0000–3FFF` | RAM2 chip `0000–3FFF` | — |
| `C000–FFFF` | RAM chip `4000–7FFF` (common) | same | same |

| R (ROM page) | `2000–3FFF` |
|---|---|
| 0 | Main ROM block B (MTX BASIC) |
| 1 | Main ROM block C |
| 2 | — |
| 3 | Main ROM block n (spare 8 K) |
| 4, 5 | — |
| 6 | ROMx (and ROMx also covers `4000–7FFF`) |
| 7 | Off-board cartridge (`ROM7` on PROG pin 2) |

### CP/M mode (`CPM` = 1)

| CPU address | P = 0 | P ≠ 0 |
|---|---|---|
| `0000–3FFF` | RAM2 chip `0000–3FFF` | — |
| `4000–7FFF` | RAM2 chip `4000–7FFF` (except when R = 6, see section 9 item 4) | — |
| `8000–BFFF` | RAM chip `0000–3FFF` | — |
| `C000–FFFF` | RAM chip `4000–7FFF` | same |

- "—" = nothing selected; with the data-bus pull-downs the CPU reads `00h`.
- P = 0 gives 48 K + 16 K common = the full 64 K, and the two modes share the same RAM chips, so in CP/M mode the 16 K that ROM mode shows as page 1 (`8000–BFFF`, P = 1) appears at `0000–3FFF`.
- The page bits are fully decoded (P3–P0 = 0 or 1), so pages 2–15 are empty until another board decodes the MTX group.
- ROM A is at chip `0000` whatever R is (since PLD rev 002; the earlier version needed an image of ROM A at chip `4000` too).

### Program image layout for the programmer
The programmer burns from chip address 0 (overview section 4). For the main ROM the 32 K image is: OS (A) at `0000`, BASIC (B) at `2000`, spare (n) at `4000`, page-1 ROM (C) at `6000`. Blocks B, n and C all run at CPU `2000`, so each is assembled with `ORG 2000h` and placed at its image offset. ROMx code runs at CPU `2000–7FFF` (R = 6) from chip `2000–7FFF`.

---

## 6. Connectors

### 6.1 Stack bus

One footprint per group, bottom side, same corner layout as the other boards. Every group passes through. The reference numbers differ from the other boards (JA1–JA8 in a different order).

| Conn | Name | Pins 1→8 | Use on this board |
|---|---|---|---|
| JA1 | ADDR | A0 … A7 | CPU drives |
| JA3 | ADDR2 | **A15** A14 … A9 **A8** (reversed) | CPU drives |
| JA2 | DATA | D0 … D7 | CPU, memories, 273; 4k7 **pull-downs** |
| JA6 | CTRL | RSTB, CLK, M1B, MREQB, IORQB, RDB, WRB, INTB | RSTB **driven** (IC9). CLK = 4M (consumed). M1/MREQ/IORQ/RD/WR from CPU. INTB → CPU, 1 k pull-up |
| JA5 | SPEC | GND, +5V, VDPINTB, IEO1, IEO2, 4M, OUT0, KBDRST | +5 V **source**. 4M = CPU CLK. OUT0 → 273 CP. KBDRST → MAX811 /MR (1 k pull-up). VDPINTB, IEO1, IEO2 pass-through |
| JA7 | PROG | –, ROM7, BUSRQ, ROMWEX, ROMCSX, RESX, ROMOEX, PWR | 1: n/c. 2: **ROM7 driven** by PLD. 3: CPU /BUSRQ (1 k up). 4: both ROMs /WE (1 k up). 5: PLD (**no pull**). 6: IC9 (1 k down). 7: both ROMs /OE (1 k down). 8: raw jack input |
| JA8 | MTX | P0 P1 P2 P3 R0 R1 R2 CPM | **Driven** by the 74AHC273; also PLD inputs |
| JA4 | AUX | 8 × not connected | Pass-through |

Notes:
- `IEO1` has **no pull-up** here. The I/O board's PIO drives it, and nothing below it in the chain is fitted, so it doesn't matter.
- This is the board that drives the MTX group, confirming the overview's guess that P0–P3 / R0–R2 are the page-select bits.

### 6.2 Jumpers and switches

| Ref | Silkscreen | Setting | Effect |
|---|---|---|---|
| J3 | EN/DIS | fitted | ROMx `/CS` from PLD (enabled) |
| J3 | | open | ROMx disabled (R10 pull-up) |
| J4 | -A13- | fitted / open | ROMx A13 = CPU A13 / GND |
| J2 | -A14- | fitted / open | ROMx A14 = CPU A14 / GND |
| SW3 | PROG TARGET | ROM ABC | Programmer writes the main ROM |
| SW3 | | ROMx | Programmer writes ROMx |
| SW1 | RESET | press | Reset (via MAX811) |
| SW2 | POWER | | Power on/off |
| J1 | GND | | Ground test point |

---

## 7. PLD (IC6, ATF20V8B) — pin use

### 7.1 Pins

| Pin | Signal | Dir | Notes |
|---|---|---|---|
| 1 | A13 | in | |
| 2 | A14 | in | |
| 3 | A15 | in | |
| 4 | MREQB | in | |
| 5–8 | P0–P3 | in | RAM page |
| 9 | R0 | in | |
| 10 | ROMCSX | in | Programmer, active high. **No pull-down** |
| 11 | — | in | Spare, unconnected |
| 13 | R1 | in | |
| 14 | R2 | in | |
| 15 | ROMA13 | out, active high | Main ROM A13 |
| 16 | ROMA14 | out, active high | Main ROM A14 |
| 17 | RAM | out | RAM /CS |
| 18 | ROM7 | out | PROG pin 2 (off-board) |
| 19 | ROMX | out | ROMx /CS via J3 |
| 20 | ROM | out | Main ROM /CS |
| 21 | SELECT | in (I/O pin used as input) | SW3 |
| 22 | RAM2 | out | RAM2 /CS |
| 23 | CPM | in | |

`/RD`, `/WR`, `/IORQ` and `/M1` aren't PLD inputs. Pin 11 is the only spare.

### 7.2 Equations

WinCUPL, `Device g20v8a`; the `.jed` is simple mode (`g20v8as`).
```
ROM6    =  R2 & R1 & !R0 ;

ROMA13  = (!ROMCSX & A13 & !R1)  #  (ROMCSX & A13) ;
ROMA14  = (!ROMCSX & A13 &  R0)  #  (ROMCSX & A14) ;

!ROM    = (ADDRESS:[0000..1fff]              & !CPM & !MREQB)
        # (ADDRESS:[2000..3fff] & ROMNO:0    & !CPM & !MREQB)
        # (ADDRESS:[2000..3fff] & ROMNO:1    & !CPM & !MREQB)
        # (ADDRESS:[2000..3fff] & ROMNO:3    & !CPM & !MREQB)
        # (ROMCSX & SELECT) ;

!ROMX   = (ADDRESS:[2000..7fff] & ROMNO:6    & !CPM & !MREQB)
        # (ROMCSX & !SELECT) ;

!RAM    = (ADDRESS:[8000..BFFF] & PAGENO:0          & !MREQB)
        # (ADDRESS:[C000..FFFF]                     & !MREQB) ;

!RAM2   = (ADDRESS:[4000..7fff] & PAGENO:0 & !ROM6 & !MREQB)
        # (ADDRESS:[8000..bfff] & PAGENO:1 & !CPM  & !MREQB)
        # (ADDRESS:[0000..3fff] & PAGENO:0 &  CPM  & !MREQB) ;

!ROM7   = (ADDRESS:[2000..3fff] & ROMNO:7    & !CPM & !MREQB) ;
```

How `ROMA13`/`ROMA14` pick the block (run mode, A13 = 1 so CPU `2000–3FFF`):

| R | R1 | R0 | ROMA14 | ROMA13 | Chip block |
|---|---|---|---|---|---|
| 0 | 0 | 0 | 0 | 1 | B `2000` |
| 1 | 0 | 1 | 1 | 1 | C `6000` |
| 3 | 1 | 1 | 1 | 0 | n `4000` |

With A13 = 0 (CPU `0000–1FFF`) both are 0, so ROM A is always chip `0000`.

- The fuse map (`.jed`, built 2024-01-17, name `v102-mtx-2`, rev 002) was decoded term by term and matches the source: RAM2 5 terms (the `!ROM6` factor expands to `!R2`, `!R1`, `R0`), ROM 4, ROMX 2 (`2000–7FFF` as `2000–3FFF/6000–7FFF` + `4000–5FFF`), RAM 2, ROM7 1, ROMA13 2, ROMA14 2. XOR bits make ROMA13 and ROMA14 active high and the rest active low. AC1 sets pin 21 as an input. Simple mode (SYN = 1, AC0 = 0). Pin 21's OLMC has no terms.
- Every run-time select is qualified by `/MREQ`, so I/O and interrupt-acknowledge cycles select nothing. Refresh cycles do select memory (the PLD can't see `/RFSH`), which is harmless as on the Z80 SBC.
- Stale comments in the source: pin 19 says "page 6 2000-3fff" (the equation is `2000–7FFF`); pin 17 says "MTX500 with 32KB fixed between 8000–FFFF" (8000–BFFF is paged).

### 7.3 History (other files in the PLD folder)
- `v102-mtx-0` (2023-12-04): reset was generated in the PLD (`RSTB` from `RESB`/`RESX`); ROMx was R = 3 at `2000–3FFF`; `ROMA14 = R0` with no `ROMA13`, so ROM A had to be duplicated at chip `4000`.
- `v102-mtx-1` (2024-01-03; its `Name` field says `v102-mtx-2`): reset moved off the PLD (now IC9), `SELECT` added, otherwise as rev 0.
- `v102-mtx-2` (2024-01-15, current): `ROMA13` added (spare block n at R = 3, no duplicate of ROM A needed), ROMx moved to R = 6 and widened to `2000–7FFF`, `ROMCSX` moved to pin 10.

---

## 8. Timing notes

- **Decode:** ATF20V8B propagation (speed grade not confirmed: the symbol says -10, the part fields say a 16V8B-15). The ROM's A13/A14 also go through the PLD, so ROM access = PLD delay + 28C256 address access. At 4 MHz (T = 250 ns) the opcode-fetch budget is roughly 220–250 ns after the PLD delay, comfortable for a 150 ns 28C256 and a 70 ns 62256.
- **Page switch:** an `OUT (00h)` changes the map at the '273's clock edge in T2 of the I/O cycle. The next opcode fetch already uses the new map, as on a real MTX, so code that switches ROM pages must run from ROM A or common RAM (`C000–FFFF`).
- **'273 clock:** `OUT0` rises at `/WR` falling plus the VDP PLD delay; data has been on the bus since T1. Comfortable.
- **Clock:** the VDP oscillator drives the CPU plus every board's `CLK` input, the stack traces and R5. With 0.15 mm tracks and no buffering, edge rates depend on the stack height (section 9, item 5).

---

## 9. Observations for the next revision

Most important first.

1. **ROM drives the bus on writes to ROM space.** `ROMOEX` holds both ROM `/OE` pins low, and the ROM selects aren't gated by `/RD`. Any write to `0000–1FFF`, or to the paged ROM window, has the ROM and the CPU driving D0–D7 for the whole cycle. RAM has the usual ~1 T-state contention on every write (`/OE` tied low, as on the Z80 SBC).
   - Fix without new parts: wire spare PLD pin 11 to `/RD` and add `!RDB` to the run-time ROM, ROMX and ROM7 terms. Drive RAM `/OE` from `/RD`.
2. **`ROMCSX` has no pull-down.** Without the programmer, PLD pin 10 floats. The ATF20V8B's pin keepers hold an undriven input at its last level, so the power-up state isn't defined. If it settled high, the main ROM (or ROMx) would be selected at every address and contend with RAM, and `ROMA13`/`ROMA14` would stop paging. Add 1 k–10 k to GND, as on the Z80 SBC (R14).
3. **Programming relies on `/MREQ` staying high.** While the programmer holds the bus, the Z80 floats `/MREQ`, and the run-time terms aren't masked by `ROMCSX`. It works because the pin keeper holds the last driven level (high). If `/MREQ` drifted low:
   - programming ROMx (`SELECT` = 0) at `0000–1FFF` would also select the main ROM, and the shared `/WE` would **write both chips**,
   - RAM/RAM2 (with `/OE` grounded) would drive the bus against the programmer's data.
   - Fix: add `!ROMCSX` to every address term (no extra pins or terms needed), and put about 10 k pull-ups on `/MREQ`, `/RD`, `/WR` (project-wide item).
4. **CP/M mode with R = 6 loses 16 K.** The `!ROM6` factor in RAM2's `4000–7FFF` term isn't qualified by `CPM`, and ROMx is off in CP/M mode, so writing `0E0h`-style values (CPM = 1, R = 6) to port 00h leaves `4000–7FFF` empty. Use `ROM6 = R2 & R1 & !R0 & !CPM`.
5. **CPU clock comes from the VDP board.** Without it there's no clock, and the VDP's oscillator drives the whole stack's `CLK` load plus R5 (470 R, about 10 mA). Matches the VDP document's item 9. Either fit a local oscillator (with the Z80 SBC's JJP1-style option), or buffer `4M` on the VDP board.
6. **74AHC273 input levels.** Its `CP` comes from the VDP board's GAL16V8 (V<sub>OH</sub> min 2.4 V), while a 74AHC input at 5 V needs about 3.5 V. It works because the lightly loaded GAL output rises well above its minimum. Fit a **74AHCT273 / 74HCT273**.
7. **Power input.** Same 12 V-on-PROG-pin-8 risk as the Z80 SBC (item 7 there), plus no reverse-polarity, fuse or TVS protection. The supply return passes through SW2 and the module's internal ground (section 4.10). Simplest: tie the jack sleeve to board GND and use SW2's second pole to switch `PWR` to the bus. Check PW1's input rating against the silkscreen "7.5–15 V".
8. **ROMx mapping and labels.** The silkscreen says "ROMx (2000-3FFF R=x)"; the PLD maps it at `2000–7FFF` for R = 6. With J2/J4 open, the 28C256 shows its first 8 K three times, and a programmer image larger than 8 K wraps and overwrites itself. Label J2/J4 with "fit for 24 K ROMx" and update the silkscreen.
9. **`/NMI` and `/WAIT` tied hard to +5 V.** They can't even be bodged into use. Use resistors, and consider putting them (and `/BUSACK`) on the bus as for the Z80 SBC (item 6 there).
10. **Data-bus pull-downs vs pull-ups.** This board reads `00h` (NOP) from undriven addresses, the Z80 SBC reads `FFh` (`RST 38h`). Either is fine, but software written for one board's unmapped reads behaves differently on the other. Pick one convention for both CPU boards.
11. **Floating inputs:** PLD pin 11 (use it for item 1), and `ROMCSX` (item 2).
12. **No buffering on the CPU bus**, as on the Z80 SBC (item 5 there).
13. **Housekeeping:**
    - IC6's symbol is ATF20V8B-10PU, but its MPN, Mouser, Arrow, description and datasheet fields are copied from the ATF16V8B-15PU. IC9's datasheet field points to a TI selection guide.
    - BoM values "ROM", "RAM", "RAM2", "ROMX" instead of part numbers (28C256, HM62256).
    - Revision note says "RAM A|B|x|C" (it's ROM). Title-block rev 001; PLD rev 002; folder `-2`.
    - Stack-connector references (JA1 ADDR, JA2 DATA, JA3 ADDR2, …) don't follow the other boards' scheme (JA1/JA11, JA2/JA22 …).
    - The folder holds `PHONO-SRC-00A-erc.rpt` (name from another project), an unreferenced `v102-con-z80.kicad_sch` (2023), `V102-MTX-2.kicad_sch-bak`, empty `output.log` and `cd4530cf-….log`, and a 3D render `V102-MTX-2.png` from January 2024.
    - PLD folder: `v102-mtx-1.PLD` carries the name `v102-mtx-2`. Stale comments in the current source (section 7.2).

---

## 10. Open questions

- Is the programmer normally left fitted? If not, what level does `ROMCSX` settle at (item 2)?
- ROMx: is `2000–7FFF` at R = 6 the intended window, and are J2/J4 normally fitted? What goes in ROMx and in main-ROM block n (R = 3), i.e. the "extensions"?
- What drives the off-board `ROM7` cartridge select (a planned cartridge board?).
- PW1: same module as the Z80 SBC? Its input range against the silkscreen's 7.5–15 V.
- Fitted speed grades: ATF20V8B (-10 or -15), 28C256, Z80.
- Whether any board will decode the MTX group (RAM pages ≥ 2).
