# NOVAZ80 I/O Board — V102-IO1-0 (Rev 000)

Design analysis from `V102-IO1-0.net` (KiCad/Eeschema 9.0.7 export, 2026-11-25), the schematic, the BoM and the PCB file (`V102-IO1-0.kicad_pcb`). ERC: 0 errors / 0 warnings. DRC: 0 violations, 0 unconnected pads, 0 footprint errors.

Title block: *NOVA Z80 Project – v102-IO1*, NOVA Embedded Solutions, drawn 2023-05-25, Rev 000.
Change notes on the schematic:
1. Added jumper to select divide by 12 or 13 for the baud master clock.
2. Jumper to select the baud master from the bus 4 MHz line or the local oscillator.
3. Added connectors for LCD/top board.
4. Connected the MTX keyboard reset to SP2, now `KBDRST`.

PLD: `V102-IO1-00.PLD` and `V102-IO1-00.jed`. The fuse map was decoded and matches the source equations (section 7).

There is a second, different I/O board, `V102-IO2-0` (82C55 PPI, 20×4 LCD, 8 push buttons, GAL16V8). It is not covered here.

---

## 0. Where this board sits in the NOVAZ80 project

The main optional I/O board, shared by the CPU boards. It adds:
- a **Z80 SIO/0** serial port, reachable over **USB** (FT232RL) or a **DB9** connector,
- a **Z80 CTC**, which also generates the serial baud clock and takes the **VDP interrupt** on channel 0 (as on a real MTX),
- a **Z80 PIO**: port A reads a **PS/2 keyboard** through a hardware deserialiser, port B is a general-purpose port,
- an 8-bit **output latch** (port C),
- decoded strobes for the **custom MTX keyboard** (10 × 8 matrix) on ports 05h/06h.

Its I/O addresses (05h–13h) follow the Memotech MTX512 map, so in the MTX configuration this board supplies the MTX's CTC and keyboard ports. It doesn't clash with the Z80 SBC's own CTC (18h) and PIO (20h).

This board is the **head of the interrupt daisy chain** (section 4.6). It takes +5 V from the stack and has no power supply of its own.

Status: built, tested and in use. Section 9 collects observations for the planned 4-layer revision.

---

## 1. Summary

| Item | Value |
|---|---|
| Serial | Z84C40 SIO/0, channel B only. USB (FT232RL) or DB9 (logic-level, inverted), chosen by jumper SW1 |
| Timers | Z84C30 CTC: ch0 = VDP interrupt, ch1/ch3 = user triggers, ch2 = baud generator for the SIO |
| Parallel | Z84C20 PIO: port A = PS/2 scan code, port B = user port J7 |
| Output latch | 74HC574 "port C" at 07h → J9 |
| Keyboard | PS/2 (receive only, 2 × 74HC595 deserialiser) and MTX 10 × 8 keyboard strobes (J6) |
| Baud clock | 24 MHz oscillator (or bus `4M`) ÷ 13 (or ÷ 12) by 74LS193 → 1.846 MHz into CTC ch2 |
| Glue | GAL16V8 PLD: I/O decode only |
| I/O ports | 05h–07h strobes/latch, 08h–0Bh CTC, 0Ch–0Fh SIO, 10h–13h PIO |
| Power | +5 V from the stack (SPEC pin 2) |
| PCB | 100 × 100 mm, 2-layer, +5 V pour on F.Cu, GND pour on B.Cu, 0.15 mm signal tracks (0.3 mm for some power) |

---

## 2. Block diagram

```
                 ┌──────── stack bus: A0–A7, D0–D7, IORQ RD WR M1 CLK RSTB INTB ────────┐
                 │                                                                      │
   A0–A7, IORQ, RD, WR ─► PLD IC4 ─┬─► CTCB (08–0B)   ─► CTC /CE
                                   ├─► SIOB (0C–0F)   ─► SIO /CE
                                   ├─► PIOB (10–13)   ─► PIO /CE
                                   ├─► PORTC (OUT 07) ─► 74HC574 CP ─► J9 PORT C
                                   └─► IN5, IN6, OUT5 ─► J6 MTX/LCD (with D0–D7, KBDRST, +5V)

 XT1 24 MHz ─JP2 1┐
 bus 4M ─────JP2 3┴─JP2 2─► 74LS193 ÷13 (JP1 open / 1-2) or ÷12 (JP1 2-3) ─► "1846K" ─► CTC CLK/TRG2
                                                                    CTC ZC/TO2 ─► SIO RxTxCB (ch B clock)

 USB J10 ─► FT232RL ─TXD──► SW1 C ┐
 DB9 pin 3 ─► U3 inv ────► SW1 A ┴─SW1 B─► SIO RxDB
 SIO TxDB ─┬─► FT232 RXD
           └─► U3 inv ─► DB9 pin 2

 PS/2 J5: CLK ─► U2 inv ─► SERCLK ─► 2×74HC595 shift clock      DATA ─► 595 SER
          SERCLK ─► D1/R1/C3 timeout (~100 µs) ─► U1 inv ─► LCLK ─► 595 latch ─► PIO PA0–7
                                                 U1 inv ─► R5/C1 ~1 µs ─► U2 inv ─► PIO /ASTB

 bus VDPINTB ─► CTC CLK/TRG0      J8: TRG1, TRG3 (1 k pull-ups), TO1
 Daisy chain: +5V ─► CTC IEI ─ IEO ─► SIO IEI ─ IEO ─► PIO IEI ─ IEO ─► bus IEO1 (→ Z80 SBC CTC)
```

---

## 3. Parts (BoM)

| Ref | Part | Function | Datasheet |
|---|---|---|---|
| IC1 | Z84C2006 (Z80 PIO, 6 MHz CMOS), DIP-40 | Keyboard / user parallel port | [Z80 PIO PS0180](http://www.zilog.com/docs/z80/ps0180.pdf) |
| IC2 | Z84C3006 (Z80 CTC, 6 MHz CMOS), DIP-28 | Timers, baud generator, VDP interrupt | [Z80 CTC PS0181](http://www.zilog.com/docs/z80/ps0181.pdf) |
| IC3 | Z84C4006 (Z80 SIO/0, 6 MHz CMOS), DIP-40 | Serial port | [Z80 SIO PS0183](http://www.zilog.com/docs/z80/ps0183.pdf), [Z80 peripherals UM0081](http://www.zilog.com/docs/z80/um0081.pdf) |
| IC4 | GAL16V8, DIP-20 | I/O decode PLD | [ATF16V8B (compatible)](http://ww1.microchip.com/downloads/en/devicedoc/atmel-0364-pld-atf16v8b-8bq-8bql-datasheet.pdf) |
| IC5, IC6 | 74HC595, DIP-16 | PS/2 serial-to-parallel (16-bit chain) | [SN74HC595](http://www.ti.com/lit/ds/symlink/sn74hc595.pdf) |
| IC8 | 74HC574N, DIP-20 | Port C output latch | [SN74HC574](https://www.ti.com/lit/ds/symlink/sn74hc574.pdf) |
| IC10 | FT232RL, SSOP-28 | USB ↔ UART | [FT232R](https://ftdichip.com/wp-content/uploads/2020/08/DS_FT232R.pdf) |
| IC11 | 74LS193, DIP-16 | Baud master divider (÷12/÷13) | [SN74LS193](http://www.ti.com/lit/ds/symlink/sn74ls193.pdf) |
| U1, U2, U3 | 74LVC2G14, SOT-23-6 | Dual Schmitt inverters (PS/2 timing, DB9 level inversion) | [SN74LVC2G14](https://www.ti.com/lit/ds/symlink/sn74lvc2g14.pdf) |
| XT1 | 24 MHz full-can DIP-14 oscillator | Baud master clock | [Typical DIP-14 oscillator](http://cdn-reichelt.de/documents/datenblatt/B400/OSZI.pdf) |
| D1 | 1N4148, SOD-123 | PS/2 timeout charge diode | [1N4148W](https://www.vishay.com/docs/85748/1n4148w.pdf) |
| J10 | USB mini-B, Würth 65100516121 | Host serial link | [Würth 65100516121](https://www.we-online.com/components/products/datasheet/65100516121.pdf) |
| J12 | DB9 female, right-angle | "RS232" (logic level, see 4.3) | — |
| J5 | 1×6 right-angle socket | PS/2 keyboard | — |
| J6 | 2×7 IDC header | "MTX/LCD": custom MTX keyboard (LCD use abandoned) | — |
| J7 | 2×9 socket | PIO port B | — |
| J8 | 1×4 socket | CTC "Timer" | — |
| J9 | 2×8 socket | Port C latch outputs | — |
| SW1 | 1×3 pin header (jumper) | SIO RxD source: USB or DB9 | — |
| JP1 | 3-pad solder jumper (open as supplied) | ÷13 / ÷12 select | — |
| JP2 | 1×3 socket (jumper) | Baud master source: 24 MHz or bus 4M | — |
| J1–J4, J11, J22, J33, J44 | 8-way "11 mm" stacking sockets (bottom side) | Stack bus (section 6) | — |
| C4–C8 | 1 µF 1206 | +5 V bypass (the only bypass caps) | — |
| C2 | 1 µF | FT232 3V3OUT decoupling | — |
| C3 / R1 | 47 nF / 2k2 | PS/2 end-of-frame timeout | — |
| C1 / R5 | 1 nF / 1 k | PS/2 strobe delay (~1 µs) | — |
| R2, R4 | 1 k | Pull-ups on CTC TRG1, TRG3 | — |
| R3, R6 | 10 k / 4k7 | VBUS sense divider → FT232 RESET# | — |

The SIO part number Z84C4006 is the SIO/0 bond-out (channel B has a combined RxTxCB clock pin and keeps DTRB and SYNCB), which matches the pin names in the netlist.

---

## 4. Subsystems

### 4.1 Address decode (IC4)
See section 7. All selects are I/O only (`/IORQ`), 8-bit decode (A0–A7). `/M1` isn't a PLD input.

### 4.2 SIO (IC3) — serial port
- `B/A` = A0, `C/D` = A1: `0Ch` ch A data, `0Dh` ch B data, `0Eh` ch A control, `0Fh` ch B control.
- `/CE` = SIOB. `/RESET` = `RSTB`. `/M1`, `/IORQ`, `/RD`, `CLK`, `/INT` from the bus.
- **Channel B** is the only channel used:
  - `RxDB` ← SW1 common (USB or DB9).
  - `TxDB` → FT232 RXD **and** U3 → DB9 pin 2, both at once.
  - `RxTxCB` ← CTC `ZC/TO2` (the baud clock, section 4.4).
  - `CTSB`, `DCDB`, `SYNCB` tied to +5 V (inactive). `DTRB`, `RTSB`, `W/RDYB` not connected. There is **no hardware flow control**, and Auto Enables must stay off (with CTS held inactive it would block the transmitter).
- **Channel A is unused:** `RxDA` tied to GND, `TxDA` open, `RxCA`/`TxCA`/`SYNCA`/`CTSA`/`DCDA` tied to +5 V.

### 4.3 Serial physical layer
- **USB:** FT232RL (IC10), same arrangement as the programmer: VCC and VCCIO on +5 V (self-powered), VBUS only feeds the R6/R3 divider into RESET# (≈ 3.4 V), so the FTDI chip is held in reset when USB is unplugged. USB doesn't power the board. CBUS0–4, DTR/RTS/CTS/DSR/DCD/RI unused. ID, TEST, AGND and shield grounded.
- **DB9 (J12):** U3 (74LVC2G14) inverts in both directions: SIO TxDB → pin 2, pin 3 → SW1 A. Pin 5 and the shell are GND. Other pins are not connected.
  - The levels are **0/5 V, inverted**, i.e. "TTL RS-232". There is no MAX232-type level shifter. Real RS-232 on pin 3 (±3 to ±15 V) exceeds the 74LVC2G14's input rating (−0.5 V to 6.5 V). See section 9, item 1.
  - Pin 2 output and pin 3 input are the DCE (female) convention, so a straight cable to a PC's DB9 male works.
- **SW1** (a 1×3 header used as a jumper): B (common) = SIO RxDB. A = DB9 (via U3). C = USB (FT232 TXD). Link B–C for USB, B–A for DB9. With no link, RxDB floats.

### 4.4 Baud clock (XT1, IC11, CTC ch2)
- **JP2** "Primary BAUD clock": 1–2 = local 24 MHz (XT1), 3–2 = bus `4M` (SPEC pin 6). The centre pin drives the 74LS193's DOWN clock.
- **IC11 74LS193** is a down counter that reloads itself: `/BO` → `/LOAD`, UP tied high, CLR tied low. Preset inputs D = 1, C = 1, B = 0, A = JP1.
  - **JP1** (solder jumper, open as supplied) sets the preset to 13 (1–2, +5 V) or 12 (3–2, GND). Silkscreen note: 1–2 "Div by 13", 3–2 "Div by 12".
  - **Why the jumper exists (designer):** different logic families of the '193 behave differently with `/BO` wired to `/LOAD`. The jumper lets any family be fitted and still give the intended division. The likely mechanism: in some families the zero state lasts only a glitch (division = preset), while in others it lasts a full clock (division = preset + 1). So the preset that gives the target division depends on the part fitted. With the fitted 74LS193, preset 13 (JP1 open or 1–2; an open LS input floats high) gives ÷13.
  - Output QD → CTC `CLK/TRG2` (IC2 pin 21), net named `1846K` (1846 kHz = 1.846 MHz, i.e. ÷13). QA–QC and `/CO` are unused.
- **24 MHz ÷ 13 = 1.846 MHz.** The CTC counts this in counter mode with time constant N, and `ZC/TO2` clocks the SIO. With the SIO in ×16 mode:

| N | Baud | | N | Baud |
|---|---|---|---|---|
| 1 | 115 385 | | 12 | 9 615 |
| 2 | 57 692 | | 24 | 4 808 |
| 3 | 38 462 | | 48 | 2 404 |
| 6 | 19 231 | | 96 | 1 202 |

  Every rate is +0.16 % from the standard value, well within tolerance.
- With the bus `4M` source: 4 MHz ÷ 13 ÷ 16 = 19 231 baud maximum (N = 1).
- The ROM sets up the CTC for **9600 baud** on `SIOCLK`. The time constant has to match the actual division:

| Actual division | Baud master | CTC time constant for 9600 (SIO ×16) | Result |
|---|---|---|---|
| ÷13 | 1.846 MHz | **12** | 9615 (+0.16 %) |
| ÷12 | 2.000 MHz | **13** | 9615 (+0.16 %) |

  If the ROM's constant doesn't match the division the board actually produces, the rate is off by about 8 % and serial fails. Check IC2 pin 21 with a frequency counter or scope after changing the '193's family or JP1.
- ÷13 is preferred: 2.0 MHz is exactly the CTC's counter-mode limit at a 4 MHz bus clock, and only ÷13 gives the higher standard rates (table above).
- **Constraint:** in counter mode the CTC's trigger input must be slower than half its `CLK` (the bus CPU clock). At 4 MHz that's 2 MHz, so 1.846 MHz is just inside. A CPU board running the bus clock below about 3.7 MHz can't count the baud master (section 9, item 4).
- Who drives `4M` on the bus is still open. The Z80 SBC only consumes it (JJP1).

### 4.5 CTC (IC2)
- `CS0` = A0, `CS1` = A1: channels 0–3 at `08h`–`0Bh`. `/CE` = CTCB. `/RESET` = `RSTB`.

| Channel | CLK/TRG | ZC/TO |
|---|---|---|
| 0 | **`VDPINTB`** (bus SPEC pin 3) | not connected |
| 1 | J8 pin 2 (`USERT1`, 1 k pull-up R2) | J8 pin 4 (`TIMER1`) |
| 2 | baud master `1846K` | SIO `RxTxCB` |
| 3 | J8 pin 3 (`USERT3`, 1 k pull-up R4) | (CTC has no TO3) |

- **VDP interrupt:** `VDPINTB` drives channel 0's trigger, as on a real MTX. Software sets channel 0 to counter mode, time constant 1, interrupt enabled, so each VDP frame interrupt becomes a CTC interrupt with its own IM2 vector. This answers the overview's open question for any machine that has this board fitted. There is no pull-up on `VDPINTB` here. *To confirm* on the VDP board.

### 4.6 Interrupt daisy chain
`+5V` → **CTC** IEI → CTC IEO → **SIO** IEI → SIO IEO → **PIO** IEI → PIO IEO → bus **`IEO1`** (SPEC pin 4).

With the Z80 SBC, the full chain is therefore:

| Priority | Device |
|---|---|
| 1 (highest) | IO1 CTC (VDP, timers, baud) |
| 2 | IO1 SIO |
| 3 | IO1 PIO (keyboard, port B) |
| 4 | Z80 SBC CTC |
| 5 | Z80 SBC PIO |
| 6 | whatever takes `IEO2` |

- The CTC's IEI is tied high, so this board **must be at the head of the chain**. Only one board in a stack can do this.
- The PIO's IEO drives `IEO1`, which the Z80 SBC also pulls up with R13 (1 k). That costs about 5 mA while IEO is low. Harmless.
- `IEO2` only passes through this board.
- All three parts drive the wired-OR `INTB` (open-drain).

### 4.7 PIO (IC1)
- `B/A` = A0, `C/D` = A1: `10h` port A data, `11h` port B data, `12h` port A control, `13h` port B control.
- `/CE` = PIOB. `/M1`, `/IORQ`, `/RD`, `CLK`, `/INT` from the bus. No reset pin (the PIO resets on `/M1` without `/RD` or `/IORQ`).
- **Port A** = PS/2 scan code (`KB0`–`KB7`) from the 74HC595s. `/ASTB` = `KBDINT`. Use **mode 1 (input)** with interrupt enabled. `ARDY` not connected.
- **Port B** = J7 (any mode). `/BSTB` = J7 pin 2 (`PBINT`), **no pull-up**. `BRDY` not connected.

### 4.8 PS/2 keyboard deserialiser
Receive-only, no CPU bit-banging: the hardware assembles each scan code and hands the PIO a byte with a strobe.

1. **Shift.** `KBDCLK` is inverted by U2 to `SERCLK`, which clocks both 74HC595s (IC5 → IC6, 16-bit chain). PS/2 data is valid on the falling clock edge, which is the 595's rising `SRCLK` edge. `KBDATA` goes straight to IC5 `SER`.
2. **End-of-frame timeout.** While clock pulses arrive, D1 charges C3 (47 nF) each time `SERCLK` goes high, and R1 (2k2) discharges it in between (τ ≈ 100 µs). C3 stays above U1's threshold during a frame (clock period 60–100 µs). About **100 µs after the last clock** it falls below, and U1 drives `LCLK` high.
3. **Latch.** `LCLK` rising clocks the 595s' output registers, so the new byte appears on PA0–PA7.
4. **Strobe.** U1's second inverter drives R5/C1 (≈ 1 µs) into U2's second inverter → `KBDINT` (`/ASTB`). `/ASTB` goes low at the start of each frame and rises about 1 µs after the latch, so the PIO captures the new byte on the rising edge and interrupts.

Bit placement after an 11-bit frame (start, D0–D7, parity, stop):

| 595 output | Frame bit | PIO |
|---|---|---|
| IC6 QC | start | not connected |
| IC6 QB, QA | D0, D1 | PA0, PA1 |
| IC5 QH … QC | D2 … D7 | PA2 … PA7 |
| IC5 QB | parity | not connected |
| IC5 QA | stop | not connected |

So port A reads the scan code byte directly.
- Each frame rewrites every used position and the latch is triggered by inactivity, so the deserialiser re-synchronises on every frame. A noise edge only corrupts that one frame.
- **Not checked:** start, parity, stop. **Not possible:** host → keyboard commands (LEDs, reset, scan-code set), because the board can't drive clock or data.
- The 595 output register is random at power-up. The first valid byte is normally the keyboard's `AAh` self-test result.
- J5 pinout: 1 DATA, 2 n/c, 3 GND, 4 +5 V, 5 CLK, 6 n/c. This is the PS/2 mini-DIN pin numbering, presumably for a PS/2 socket breakout. **No pull-ups on CLK or DATA** on this board (section 9, item 3).

### 4.9 Port C latch (IC8)
- 74HC574, D0–D7 from the bus, `CP` = PLD `PORTC` (low during `OUT (07h)`, rising at the end of `/WR`), `/OE` tied low.
- Q0–Q7 → J9 even pins. **Write-only, no reset**: outputs are random at power-up until the first `OUT (07h)`.

### 4.10 MTX keyboard connector (J6, "MTX/LCD")
D0–D7 directly from the data bus, plus PLD strobes `IN5` (read 05h), `IN6` (read 06h), `OUT5` (write 05h), `KBDRST`, +5 V and GND.

- **Use (designer):** the interface to the **custom MTX keyboard**, a **10 × 8 matrix**. It was also meant for an LCD peripheral, but that attempt failed, so J6 is the MTX keyboard connector in practice.
- Ports 05h/06h are the MTX512 keyboard ports. Expected use: `OUT (05h)` latches the 8 drive lines; `IN (05h)` reads 8 sense lines and `IN (06h)` reads the remaining 2. The drive latch and sense buffers are on the keyboard side. *To confirm with the keyboard's design.*
- `KBDRST` (SPEC pin 8) carries the keyboard's reset key to the CPU board's MAX811 `/MR`.
- D0–D7 go out on the cable unbuffered (section 9, item 8).

### 4.11 Power
- +5 V only, from SPEC pin 2. No regulator, no switch.
- Bypass: C4–C8 (1 µF) for 11 ICs plus the oscillator.
- Copper: +5 V pour on F.Cu, GND pour on B.Cu.

---

## 5. I/O map (from the PLD)

| Port | Read | Write | Device |
|---|---|---|---|
| `05h` | `IN5` strobe (J6 pin 4) | `OUT5` strobe (J6 pin 3) | MTX keyboard sense / drive |
| `06h` | `IN6` strobe (J6 pin 2) | — | MTX keyboard sense (high bits) |
| `07h` | — | Port C latch → J9 | 74HC574 |
| `08h`–`0Bh` | CTC ch 0–3 | CTC ch 0–3 | IC2 |
| `0Ch` / `0Dh` | SIO ch A / ch B data | same | IC3 |
| `0Eh` / `0Fh` | SIO ch A / ch B control | same | IC3 |
| `10h` / `11h` | PIO port A (keyboard) / port B data | same | IC1 |
| `12h` / `13h` | PIO port A / port B control | same | IC1 |

- Decode is on A0–A7 only, so the map repeats for any value of A8–A15.
- No overlap with the Z80 SBC (CTC `18h`, PIO `20h`).
- 05h–0Bh match the MTX512 assignments (keyboard and CTC). *Confirm 0Ch–13h against the MTX board's map when it's documented.*

---

## 6. Connectors

### 6.1 Stack bus
One footprint per group, bottom side, same corner layout as the Z80 SBC. Every group passes through.

| Corner | Connectors |
|---|---|
| Top-left | J1 ADDR, J11 ADDR2 |
| Top-right | J2 SPEC, J22 PROG |
| Bottom-left | J4 DATA, J44 AUX (silkscreen "SPARE") |
| Bottom-right | J3 CTRL, J33 MTX |

| Conn | Name | Pins 1→8 | Use on this board |
|---|---|---|---|
| J1 | ADDR | A0 … A7 | A0/A1 → PIO, CTC, SIO; A0–A7 → PLD |
| J11 | ADDR2 | A15 … A8 (reversed) | Pass-through |
| J4 | DATA | D0 … D7 | PIO, CTC, SIO, 74HC574, J6 |
| J3 | CTRL | RSTB, CLK, M1B, MREQB, IORQB, RDB, WRB, INTB | RSTB → CTC, SIO reset. CLK, M1B → PIO/CTC/SIO. IORQB, RDB → peripherals + PLD. WRB → PLD only. INTB ← all three. MREQB pass-through |
| J2 | SPEC | GND, +5V, VDPINTB, IEO1, IEO2, 4M, OUT0, KBDRST | +5 V **in**. VDPINTB → CTC TRG0. IEO1 ← PIO IEO. 4M → JP2-3. KBDRST ↔ J6-13. IEO2, OUT0 pass-through |
| J22 | PROG | –, ROM7, BUSRQ, ROMWEX, ROMCSX, RESX, ROMOEX, PWR | Pass-through only (PWR carries 12 V from the CPU board) |
| J33 | MTX | P0 P1 P2 P3 R0 R1 R2 CPM | Pass-through |
| J44 | AUX | 8 × not connected | Pass-through (programmer SPI on pins 3–5) |

### 6.2 J5 — PS/2 (1×6 right-angle socket)
| Pin | Signal |
|---|---|
| 1 | KBDATA → IC5 SER |
| 2 | n/c |
| 3 | GND |
| 4 | +5 V |
| 5 | KBDCLK → U2 |
| 6 | n/c |

### 6.3 J6 — MTX keyboard ("MTX/LCD", 2×7 IDC)
| Pin | Signal | Pin | Signal |
|---|---|---|---|
| 1 | GND | 2 | IN6 (read 06h, active low) |
| 3 | OUT5 (write 05h, active low) | 4 | IN5 (read 05h, active low) |
| 5 | D0 | 6 | D7 |
| 7 | D1 | 8 | D6 |
| 9 | D2 | 10 | D5 |
| 11 | D3 | 12 | D4 |
| 13 | KBDRST | 14 | +5 V |

### 6.4 J7 — PIO port B (2×9)
| Pins | Signal |
|---|---|
| 2 | /BSTB (`PBINT`, no pull-up) |
| 4, 6, 8 … 18 | PB0, PB1 … PB7 |
| 1, 3, 5 … 17 | GND |

No +5 V, no BRDY.

### 6.5 J8 — Timer (1×4)
| Pin | Signal |
|---|---|
| 1 | GND |
| 2 | CTC CLK/TRG1 (1 k pull-up) |
| 3 | CTC CLK/TRG3 (1 k pull-up) |
| 4 | CTC ZC/TO1 |

This is **not** the same pinout as the Z80 SBC's J6 Timer header (TR0, TR1, GND, TO0).

### 6.6 J9 — Port C (2×8)
| Pins | Signal |
|---|---|
| 2, 4 … 16 | Q0 … Q7 |
| 1, 3 … 15 | GND |

### 6.7 J12 — DB9 female
| Pin | Signal |
|---|---|
| 2 | Data out (SIO TxDB, inverted, 0/5 V) |
| 3 | Data in (→ inverted → SW1 A) |
| 5, shell | GND |
| 1, 4, 6–9 | n/c |

### 6.8 Jumpers
| Ref | Setting | Effect |
|---|---|---|
| SW1 | B–C | SIO RxD from USB |
| SW1 | B–A | SIO RxD from DB9 |
| JP2 | 1–2 | Baud master = 24 MHz local |
| JP2 | 2–3 | Baud master = bus `4M` |
| JP1 | open or 1–2 | ÷13 |
| JP1 | 2–3 | ÷12 |

---

## 7. PLD (IC4, GAL16V8) — pin use

All 18 signal pins are used. There are no spares.

| Pin | Signal | Dir | Notes |
|---|---|---|---|
| 1 | IORQB | in | |
| 2–9 | A0–A7 | in | `FIELD ADDR = [A7..A0]` |
| 11 | RDB | in | |
| 12 | WRB | in (I/O pin used as input) | |
| 13 | SIOB | out | SIO /CE |
| 14 | PIOB | out | PIO /CE |
| 15 | CTCB | out | CTC /CE |
| 16 | IN5 | out | J6-4 |
| 17 | IN6 | out | J6-2 |
| 18 | OUT5 | out | J6-3 |
| 19 | PORTCOUT | out | 74HC574 CP (net `PORTC`) |

Equations (WinCUPL, `Device g16v8a`; the `.jed` is simple mode, `g16v8as`):
```
!PORTCOUT = ADDR:7       & !IORQB & !WRB ;   /* OUT 07h          */
!CTCB     = ADDR:[8..B]  & !IORQB ;          /* CTC  08-0B       */
!PIOB     = ADDR:[10..13]& !IORQB ;          /* PIO  10-13       */
!SIOB     = ADDR:[C..F]  & !IORQB ;          /* SIO  0C-0F       */
!IN5      = ADDR:5       & !IORQB & !RDB ;   /* IN  05h          */
!IN6      = ADDR:6       & !IORQB & !RDB ;   /* IN  06h          */
!OUT5     = ADDR:5       & !IORQB & !WRB ;   /* OUT 05h          */
```
- The fuse map (`.jed`, built 2023-07-04) was decoded term by term: one product term per output, all seven match the source, all outputs active low (XOR bits 0), simple mode (SYN = 1, AC0 = 0), signature "00". The `.PLD` file was saved later (2023-07-26) with the same logic.
- Peripheral selects aren't gated by `/RD`, `/WR` or `/M1`. The Zilog parts use `/RD` and `/M1` themselves, so that's correct.
- `MREQB` isn't needed (I/O only).

---

## 8. Timing notes

- **Decode delay:** GAL16V8 propagation (speed grade not recorded, typically 10–25 ns) between `/IORQ`/address and the selects. Z80 I/O cycles insert an automatic wait state, so this is comfortable at 4 MHz.
- **Port C latch:** the clock edge is the end of `/WR` (or `/IORQ`) plus the PLD delay. The Z80 holds data for a while after `/WR` rises, which comfortably covers the HC574's few-ns hold time plus the PLD delay.
- **Interrupt acknowledge:** CTC/PIO/SIO selects can coincide with an INTA cycle if the PC low byte matches. All three recognise `/M1` + `/IORQ` as INTA and ignore `/CE`. Benign, same as the Z80 SBC.
- **74LS193 at 24 MHz:** the LS193's guaranteed minimum maximum count rate is 25 MHz, so 24 MHz is just inside. The `/BO` → `/LOAD` reload is asynchronous and must complete inside a 21 ns half-period. It works on the built board, but the margin is thin (section 9, item 5).
- **CTC counter input:** 1.846 MHz against a 2 MHz limit at a 4 MHz bus clock (section 4.4).
- **SIO clock at N = 1:** `ZC/TO2` pulses are about one CPU clock wide. At 115 200 baud with a 4 MHz bus clock, check the SIO's minimum RxTxC high/low times against the CTC's output pulse. Lower rates have plenty of margin.
- **PS/2 timeout:** a frame is latched about 100 µs after its last clock edge. Keyboards normally leave much longer gaps between bytes of multi-byte codes (`E0`, `F0` sequences). The CPU then has until the next byte's latch, typically a millisecond or more, to read port A.

---

## 9. Observations for the next revision

Most important first.

1. **DB9 is logic level only.** There's no RS-232 transceiver. It works with the designer's HP Deskpro Mini serial port, but only outside spec, on both sides:
   - **Pin 3 in:** a real RS-232 driver (±5 to ±12 V) exceeds the 74LVC2G14's input rating (−0.5 V to 6.5 V). The negative swing is clamped by the input diode, limited only by the PC driver's current limit. The positive swing has no clamp at all, because LVC inputs are over-voltage tolerant with no diode to V<sub>CC</sub>. Modern PCs often use low-voltage transceivers (about ±5.5 V), which may be why it survives, but it's stressing the part.
   - **Pin 2 out:** 0/5 V instead of ±5 V or more. Most PC receivers switch at about 1.3 V, so it works.
   - Fix: a MAX3232-class transceiver. Minimum: about 10 k in series with pin 3 plus a Schottky clamp to +5 V, and a "TTL-level" label.
2. **Floating inputs:** SIO RxDB when SW1 has no link, PIO `/BSTB` (J7 pin 2), PS/2 CLK/DATA when no keyboard is plugged in (noise on CLK can latch garbage scan codes and raise interrupts), CTC TRG0 if nothing pulls `VDPINTB` up, and the 74LS193's A input with JP1 open. Add pull-ups (about 10 k) and supply JP1 bridged 1–2.
3. **PS/2 pull-ups.** The PS/2 interface expects pull-ups on CLK and DATA. It works with the current keyboard, but adding about 4k7 to +5 V on each would make it work with keyboards that rely on the host's pull-ups.
4. **Baud generator depends on the bus CLK.** The CTC can only count the 1.846 MHz baud master if the bus `CLK` is above about 3.7 MHz. With a slower CPU clock (for example on the 6502 SBC) the serial port won't work at all. A 1.8432 MHz oscillator driving `RxTxCB` directly, or driving CTC ch2 with a slower master, would remove the dependency.
5. **Simplify the baud master.** The '193's division depends on its logic family (hence JP1), and the LS part runs close to its limit at 24 MHz. A 1.8432 MHz oscillator gives exact standard rates and removes XT1 (24 MHz), the 74LS193, JP1 and JP2. It also makes the ROM's CTC time constant independent of which counter is fitted.
6. **Almost no decoupling.** Five 1 µF caps for eleven ICs plus a 24 MHz oscillator. Add 100 nF at each IC, especially at XT1 and the 74LS193.
7. **SIO channel A wasted.** Channel A could provide a second serial port (or the TTL DB9 could move to channel A, leaving channel B for USB) instead of a jumper choosing one receive source. Bringing out RTS/CTS would allow hardware flow control at 115 200 baud.
8. **Unbuffered data bus on a cable.** J6 carries D0–D7 to the MTX keyboard with no buffer. A long cable adds load and noise to the CPU's data bus. A 74HCT245 enabled by the IN5/IN6/OUT5 strobes would isolate it. The silkscreen and schematic name "MTX/LCD" can become "MTX KBD", since the LCD use was dropped.
9. **Port C has no reset.** Its outputs are random at power-up. Drive `/OE` from a reset-cleared flag, or use a latch with a clear input (for example 74HC273 with `RSTB`).
10. **Timer header pinout differs from the Z80 SBC's.** Use one pinout for both boards.
11. **Head-of-chain is fixed.** CTC IEI is hard-wired high. A jumper to take IEI from the bus instead would let another board sit above it.
12. **Two FTDI devices on one PC.** `uploadROM.py` picks the programmer by "Z80" in the FTDI serial number. Make sure this board's FT232 serial number doesn't contain "Z80", or the script will find two ports and abort.
13. **Housekeeping:** the folder holds `PHONO-SRC-00A-erc.rpt` (name left over from another project) and an extension-less file `V102-IO1-0` (an old 2023 BoM CSV). The 24 MHz value is recorded, but the GAL16V8 speed grade isn't. The PLD source's `Company` field is `xxx`.

---

## 10. Open questions

- MTX keyboard (10 × 8): which drive/sense bits map to IN5/IN6/OUT5, and whether it buffers D0–D7 on its side.
- The CTC time constant in the current ROM (12 for ÷13, 13 for ÷12) and the actual division measured on IC2 pin 21.
- Who drives the bus `4M` line (JP2 option 2–3).
- Is `VDPINTB` pulled up on the VDP board?
- How the 6502 SBC works with this board's Zilog peripherals: they need Z80 `/M1` timing, and the daisy chain relies on the CPU fetching `RETI` (`ED 4D`) to clear each device's interrupt-under-service flag. A 6502 never does, so after the first interrupt lower-priority devices would stay blocked unless the 6502 board's PLD emulates it.
- Port addresses 0Ch–13h versus the MTX512's own map (confirm with the MTX board).
