# NOVAZ80 ROM Programmer 2 (3-pad) — V102-PR2-0 (Rev 000)

Design analysis from `V102-PR2-0.net` (KiCad/Eeschema 9.0.7 export, 2026-11-25), the schematic (root sheet + `v102-con-pr2.kicad_sch` bus sheet), the BoM, the PCB file (`V102-PR2-0.kicad_pcb`) and the MCU firmware `ISP_standard.cpp`. DRC: 0 violations, 0 unconnected pads.

Title block: *NOVA Z80 Project – v102-PR2*, NOVA Embedded Solutions, drawn 2023-06-03, Rev 000. No revision notes.

Host side: the same `uploadROM.py` and batch file as V102-PR1-2 (see that document, section 7). The serial protocol is the same, so the change of programmer is transparent to the host.

PLD: none on this board. The programmer lines it drives are decoded by the CPU boards' PLDs (`v102-z80-00`, `v102-6502-00`, `v102-mtx-2`), which were re-checked for this document; behaviour is as recorded in each CPU board's document.

---

## 0. Where this board sits in the NOVAZ80 project

The **original, slow** in-circuit ROM programmer, and the predecessor of V102-PR1-2. It does the same job (burn the CPU board's EEPROM through the stack bus) but differs in two big ways:

1. **Three pads side by side.** Instead of being one square board in a stack, it is a 310 × 111 mm board with three NOVAZ80 board footprints ("PAD A", "PAD B", "PAD C"). All three pads are wired in parallel, so it is also a **3-wide backplane**: boards on different pads share one bus, and each pad can still carry its own stack.
2. **Slow bus drive.** The MCU (ATmega8) reaches A0–A15 and D0–D7 through **three PCF8574 I²C port expanders**, not through its own ports. Every bus access is an I²C transaction, which is what makes full-ROM uploads painfully slow (section 6.5).

It is also compatible with the v101 board family, which used a slightly different connector arrangement (section 5.2).

Status: built and used; superseded for speed by V102-PR1-2. Section 8 lists observations.

---

## 1. Summary

| Item | Value |
|---|---|
| MCU | ATmega8, TQFP-32, 16 MHz crystal |
| USB | FT232RL, self-powered (same arrangement as PR1) |
| Image buffer | 23LC1024 SPI SRAM (128 KB) per the BoM; firmware also supports 23LC512 |
| Bus drive | 3 × PCF8574(T) I²C expanders: DATA `0x24`, ADHI `0x26`, ADLO `0x27` |
| ROM control lines | Driven directly by MCU port D (ROMCSX, ROMWEX, ROMOEX, BUSRQ, RESX) |
| Max image | 32 KB (firmware forces A15 = 0) |
| Write mode | Byte mode with DATA polling (page-write routine present but unused) |
| Power | +5 V **from the bus only**. The barrel jack feeds the bus `PWR` line, not this board |
| PCB | 310 × 111 mm, 2-layer, +5 V pour top, GND pour bottom, 0.15 mm signal / 0.3 mm power tracks |

---

## 2. Block diagram

```
     USB mini-B J7
          │ D+/D-       VBUS ─R8 4k7─┬─R7 10k─ GND
          ▼                          │
   ┌─────────────┐  RESET# ◄─────────┘ (FTDI held in reset when USB unplugged)
   │  FT232RL    │ TXD ──► PD0/RXD
   │  IC2        │ RXD ◄── PD1/TXD
   │             │ DTR ──SW1──C3 100n──► RESET (auto-reset, switchable)
   └─────────────┘
                         ┌──────────────────────┐
   16 MHz Y1 ───────────►│     ATmega8  IC1     │
                         │                      │  I²C 1k pull-ups (R9, R10)
   23LC1024 IC3 ◄─SPI───►│ PB2-5        PC4/PC5 ├──SDA/SCL──┬──► IC6 PCF8574 0x27 ─► A0–A7
                         │                      │           ├──► IC5 PCF8574 0x26 ─► A8–A15
                         │ PB0 RED  PB1 BLUE    │           └──► IC4 PCF8574 0x24 ◄─► D0–D7
                         │ PD2 ROMCSX PD3 ROMWEX├──────────────────────────► PROG, ICPP
                         │ PD5 ROMOEX PD6 BUSRQ │
                         │ PD7 RESX             │
                         └──────────────────────┘
   All bus nets ──► PAD A ═ PAD B ═ PAD C (paralleled)
   Barrel jack J1 ──► PWR (PROG pin 8, ICPP pin 2) ──► CPU board's power input
   +5 V ◄── SPEC pin 2 (from the CPU board's DC-DC)
```

---

## 3. Parts (BoM)

| Ref | Part | Function | Datasheet |
|---|---|---|---|
| IC1 | ATmega8, TQFP-32 | Controller | [ATmega8](https://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-2486-8-bit-AVR-microcontroller-ATmega8_L_datasheet.pdf) |
| IC2 | FT232RL, SSOP-28 | USB ↔ UART | [FT232R](https://ftdichip.com/wp-content/uploads/2020/08/DS_FT232R.pdf) |
| IC3 | 23LC1024, SOIC-8 | 128 KB SPI SRAM image buffer | [23LC1024](https://ww1.microchip.com/downloads/en/DeviceDoc/20005142C.pdf) |
| IC4, IC5, IC6 | PCF8574 (T), SOIC-16W | I²C 8-bit quasi-bidirectional ports: DATA, ADHI, ADLO | [PCF8574/PCF8574A](https://www.nxp.com/docs/en/data-sheet/PCF8574_PCF8574A.pdf) |
| Y1, C1, C2 | 16 MHz HC49-SD + 2 × 22 pF | MCU clock | — |
| C3 | 100 nF | DTR auto-reset coupling | — |
| C4–C8 | 1 µF | +5 V bypass ("position adjacent to ICs") | — |
| C9 | 100 nF | FT232 3V3OUT decoupling | — |
| D1 / R1 | Green LED / 470 R | +5 V present | — |
| D2 / R3 | Blue LED / 470 R | Status (PB1) | — |
| D3 / R4 | Red LED / 470 R | Status (PB0) | — |
| R2 | 10 k | MCU RESET pull-up | — |
| R5 | 1 k | SRAM /CS pull-up | — |
| R6 | 1 k | SRAM SIO2 pull-up | — |
| R7, R8 | 10 k / 4k7 | VBUS sense divider → FT232 RESET# | — |
| R9, R10 | 1 k | I²C SDA / SCL pull-ups | — |
| SW1 | SPDT slide (used as SPST) | DTR auto-reset on/off | — |
| J1 | Barrel jack with switch (Würth 6941xx301002) | Stack power input onto `PWR`. Silkscreen "DC IN – 7.5V to 18V" | — |
| J6 | 2×3 IDC horizontal "ICSP" | AVR ISP | — |
| J7 | USB mini-B (Würth 65100516121) | Host link | — |
| JA/JB/JC 1–444 | 8-way "11 mm" stacking sockets, 12 per pad | Bus (section 5) | — |
| JA5, JB5, JC5 | 1×15 pin header "ICPP" | `GND-PWR-ADDRHI-PROG` (section 5.2) | — |

Housekeeping: IC1's symbol is an ATmega168A-A (value changed to ATmega8) and its datasheet field points to the ATmega48A/88A/168A datasheet. IC4–IC6 descriptions say "PCF8574A" but the value and the firmware's `IO_TYPE 2` are the plain PCF8574(T).

---

## 4. Subsystems

### 4.1 Microcontroller (IC1, ATmega8)
- 16 MHz crystal, 22 pF loads. RESET: 10 k pull-up R2, also to ICSP pin 2 and via C3/SW1 to FT232 DTR.
- VCC, AVCC and AREF tied to +5 V. ADC unused (ADC6/7, PC0–PC3, PD4 unconnected).
- **Fuses** (schematic and silkscreen): LF 0xBF, HF 0xC4, LB 0xCF. Decoded for the ATmega8:
  - LF 0xBF → CKSEL = 1111, SUT = 11 (external crystal, slow-rising power), **BODEN programmed, BODLEVEL = 1 (2.7 V)**.
  - HF 0xC4 → SPIEN programmed, **CKOPT programmed** (full-swing oscillator, needed above 8 MHz), EESAVE programmed, BOOTSZ = 10 (256-word / 512-byte boot section), **BOOTRST programmed** (reset enters the bootloader). WDTON and RSTDISBL unprogrammed.
  - LB 0xCF → BLB1 = 00 (boot section protected from the application), no memory lock. Typical Arduino-bootloader settings.
- So, as on PR1, firmware is normally uploaded over USB via a serial bootloader with SW1 set for auto-reset; ICSP is the fallback.

### 4.2 USB-serial (IC2, FT232RL)
Same as PR1: VCC and VCCIO on the board's +5 V, VBUS only drives the R8/R7 divider into RESET#, so the FTDI chip is held in reset when USB is unplugged. **USB does not power the board.** TXD → PD0, RXD ← PD1. DTR → SW1 → C3 → RESET. CBUS0–4 and the modem lines are unused.

Unlike PR1, the UART pins **aren't shared with ISP** (the ATmega8 programs through its SPI pins), so USB can stay plugged in while ISP-programming.

The host script finds the programmer by "Z80" in the FT232 serial number, so this board's FT232 EEPROM must carry that string too (section 8, item 3).

### 4.3 Image buffer (IC3)
- Hardware SPI: /CS = PB2 (/SS, 1 k pull-up R5), MOSI = PB3, MISO = PB4, SCK = PB5. /HOLD tied to +5 V, SIO2 pulled up (R6): plain SPI mode.
- The SPI bus is shared with ICSP J6. R5 keeps the SRAM deselected while the MCU is held in reset, so ISP works with the SRAM fitted.
- The SPI bus does **not** reach the AUX connector (the AUX pins are pass-through only, unlike PR1).
- Firmware: `SRAM_23LC SRAM(&SPI, 10, …)`; Arduino pin 10 = PB2 in the standard ATmega8 map. ✓
- The 23LC512 uses 16-bit addresses and the 23LC1024 24-bit, so the firmware's `SRAM_TYPE` **must match the fitted chip** (section 6.1).

### 4.4 Bus port expanders (IC4–IC6, PCF8574)
- I²C on PC4/SDA and PC5/SCL, 1 k pull-ups (R9, R10). `/INT` outputs unused.
- Addresses set by A2–A0 straps. The schematic notes both variants:

| IC | Role | A2 A1 A0 | PCF8574T (`IO_TYPE 2`) | PCF8574AT (`IO_TYPE 1`) | Bus lines |
|---|---|---|---|---|---|
| IC4 | DATA | 1 0 0 | `0x24` | `0x3C` | D0–D7 (P0–P7) |
| IC5 | ADHI | 1 1 0 | `0x26` | `0x3E` | A8–A15 (P0–P7) |
| IC6 | ADLO | 1 1 1 | `0x27` | `0x3F` | A0–A7 (P0–P7) |

- **The PCF8574 outputs are quasi-bidirectional.** A `0` is a strong sink (up to about 25 mA). A `1` is only a weak current source (roughly 30–300 µA, about 100 µA typical), with a brief strong pull-up during the I²C acknowledge that writes it. Writing `FFh` turns a port into an "input" with weak pull-ups. Consequences:
  - The card never drives the address or data bus hard high. With CMOS loads that's fine, and the Z80 and 6502 SBCs' 4k7 data pull-ups help.
  - **The MTX board has 4k7 data pull-downs.** A ~100 µA weak high into 4k7 only reaches about 0.5 V, so `1` bits written to an MTX ROM are likely to be read by the EEPROM as `0`. Expect verify failures on the MTX board (section 8, item 1).
  - At power-up all 24 pins sit at weak-high, so the card places ~100 µA pull-ups on A0–A15 and D0–D7 at all times, even while the target runs. Harmless.
  - A0–A7 and D0–D7 never float when the CPU releases the bus, which is a small improvement over PR1.

### 4.5 ROM control lines
Driven directly from port D (push-pull), same polarities as PR1:

| Line | MCU pin | Arduino pin | PROG pin | ICPP pin |
|---|---|---|---|---|
| ROMCSX | PD2 | 2 | 5 | 13 |
| ROMWEX | PD3 | 3 | 4 | 12 |
| ROMOEX | PD5 | 5 | 7 | 15 |
| BUSRQ | PD6 | 6 | 3 | 11 |
| RESX | PD7 | 7 | 6 | 14 |

These match the firmware's `#define`s. `#define LED 4` (PD4) is unused and PD4 is unconnected.

### 4.6 Power
- **+5 V comes only from the bus** (SPEC pin 2 on every pad), i.e. from the CPU board's DC-DC. There is no regulator on this board.
- **J1 doesn't power this board.** Its centre pin goes to `PWR` (PROG pin 8 on all three pads and ICPP pin 2); sleeve and switch contact go to GND. `PWR` is the CPU board's raw jack input (Z80 SBC, 6502 SBC, MTX), so J1 is an **alternative power entry for the whole machine**: it feeds the CPU board's power switch and 5 V module, which then powers this card through SPEC pin 2.
  - Without a CPU board fitted, the card is unpowered even with J1 plugged in.
  - On the MTX board the jack sleeve isn't board GND; through PR2 the return path is board GND directly, which bypasses SW2's second pole. That's fine electrically.
- D1 (green) shows +5 V present.
- Bypass: five 1 µF for six ICs. Placement: C4/C6 at IC4/IC6, C7 near IC5, C8 between IC2 and IC3, C5 at IC3. IC1 has no capacitor right at its pins (nearest about 10 mm).

### 4.7 Indicators

| LED | Drive | Meaning |
|---|---|---|
| D1 green | +5 V via 470 R | Power |
| D3 red | PB0 via 470 R | Status (6.3) |
| D2 blue | PB1 via 470 R | Status (6.3) |

### 4.8 ICSP (J6)
1 GND, 2 RST, 3 MOSI (PB3), 4 SCK (PB5), 5 **+5 V direct**, 6 MISO (PB4).
Same mirrored-pin layout as PR1's J6 (standard 6-pin ISP numbered *n* ↔ 7−*n*), but carrying MOSI/MISO, as the ATmega8 requires. Pin 5 has **no jumper**: an ISP tool that supplies power would back-feed the whole stack's +5 V rail. There's no JTAG (the ATmega8 has none).

---

## 5. Target-bus connectors

### 5.1 Layout

Three identical pads at 105 mm pitch along the board (A left, B middle, C right). Each pad is the standard NOVAZ80 square footprint with four corner clusters, sockets on the bottom side. Every net is common to all three pads (section 5.3).

The programmer electronics (MCU, FT232, SRAM, expanders, USB, ICSP, SW1, LEDs) sit on the **top side inside pad C's area**. The barrel jack is on top inside pad B's area. Silkscreen: "IN-CIRCUIT PROGRAMMER", "USB INTERFACE TO PC", "MCU", "TARGET", "DESIGN REF: V102-PR2-0", "NOVAZ80 PAD "A/B/C"".

Per pad, the corner clusters are (pad A references; B and C use JB/JC):

| Corner | Two parallel rows (2.54 mm apart) | Third row at 90° | Silkscreen |
|---|---|---|---|
| Top-left | JA1 ADDR (A0–A7), JA111 ADDR2 (A15…A8) | JA11 ADDR (duplicate of JA1) | ADDRLO / ADDRHI |
| Top-right | JA2 SPEC, JA222 PROG | JA22 SPEC (duplicate of JA2) | SPEC / PROG |
| Bottom-left | JA4 DATA, JA444 AUX | JA44 DATA (duplicate of JA4) | DATA / AUX |
| Bottom-right | JA3 CTRL, JA333 MTX | JA33 CTRL (duplicate of JA3) | CTRL / MTX |

Plus **JA5 "ICPP"**, a 1×15 header along the top edge of the pad, silkscreened `GND-PWR-ADDRHI-PROG`.

Note the reference names are swapped relative to PR1: on PR1, J11 = ADDR2 and J111 = the ADDR duplicate; here X11 = the ADDR duplicate and X111 = ADDR2.

### 5.2 v101 compatibility
The designer states the board is compatible with the v101 variant, which used a slightly different connector. The PCB offers two connection patterns per pad:
- **v102:** the two parallel rows in each corner (ADDR/ADDR2, SPEC/PROG, DATA/AUX, CTRL/MTX).
- **The 90° rows (ADDR, SPEC, DATA, CTRL) plus the ICPP header** (GND, PWR, A8–A15, BUSRQ, ROMWEX, ROMCSX, RESX, ROMOEX), which together carry everything the programmer needs without the PROG and ADDR2 rows.

**Confirmed by the designer:** the second pattern is the v101 interface. The same arrangement on PR1 (J5 ICPP and the 90° rows) is therefore also the v101 connection.

### 5.3 Pin map (identical on all three pads)

| Conn | Name | Pins 1→8 | Connected on this board |
|---|---|---|---|
| X1 / X11 | ADDR | A0 … A7 | IC6 (ADLO) P0–P7 |
| X111 | ADDR2 | **A15** A14 … A9 **A8** (reversed) | IC5 (ADHI) P7…P0 |
| X4 / X44 | DATA | D0 … D7 | IC4 (DATA) P0–P7 |
| X222 | PROG | SP3, ROM7, BUSRQ, ROMWEX, ROMCSX, RESX, ROMOEX, PWR | 3–7 to MCU (4.5); 8 = J1 centre; 1, 2 pass-through |
| X2 / X22 | SPEC | GND, +5V, VDPINTB, IEO1, IEO2, 4M, OUT0, KBDRST | Power in; rest pass-through |
| X3 / X33 | CTRL | RSTB, CLK, M1B, MREQB, IORQB, RDB, WRB, INTB | Pass-through |
| X333 | MTX | P0 P1 P2 P3 R0 R1 R2 CPM | Pass-through |
| X444 | AUX | AUX1 … AUX8 | Pass-through (no SPI here) |

**X5 ICPP (1×15):** 1 GND, 2 PWR, 3–10 A8–A15, 11 BUSRQ, 12 ROMWEX, 13 ROMCSX, 14 RESX, 15 ROMOEX. Identical to PR1's J5.

### 5.4 What "paralleled pads" means in use
- Boards on pads A, B and C form **one machine on one bus**. Example: a CPU board on A, the I/O board on B, the VDP board on C, each optionally with more boards stacked above. All the stacking rules still apply (one CPU board per machine, one source of each driven signal such as `4M`, `OUT0`, `IEO1`).
- It is **not** a gang programmer: three CPU boards on three pads would fight on the address, data and control buses and the daisy chain. *To confirm with the designer that gang programming was never an intended use.*
- Tall parts on this board (barrel jack J1 under pad B; USB J7, ICSP J6 and SW1 under pad C) sit under any board stacked on those pads. Check clearance against the 11 mm sockets.

---

## 6. Firmware (`ISP_standard.cpp`)

Arduino framework for the ATmega8 (register names `TIMSK`, not `TIMSK1`). Libraries: `Wire`, `SPI`, `SRAM_23LC`. `LiquidCrystal_I2C` is included but unused.

### 6.1 Build switches

| Define | Value in file | Meaning |
|---|---|---|
| `SRAM_TYPE` | 512 | 23LC512. Comment: "1024 for all (4) programmers EXCEPT 512 for green and stacking white" |
| `IO_TYPE` | 2 | PCF8574T addresses (`0x24/26/27`). 1 = PCF8574AT (`0x3C/3E/3F`), "green" board only |
| `BAUD_RATE` | 57600 | Must match `uploadROM.py` |
| `VERIFY_STEP` | 10 | Echo every 10th byte |
| `VERIFY_ATTEMPTS` | 1000 | Read retries per byte during verify |
| `ATTEMP_DELAY` | 1 ms | Delay between retries |
| `T_WRITE_SETUP/HOLD` | 1 µs | |
| `T_READ_SETUP/HOLD` | 2 µs | |

The comment implies four programmers built from this design family with different fits:

| Board | SRAM | Expanders | `SRAM_TYPE` | `IO_TYPE` |
|---|---|---|---|---|
| "Green" | 23LC512 | PCF8574AT | 512 | 1 |
| "Stacking white" | 23LC512 | PCF8574T | 512 | 2 |
| Others (incl. this BoM) | 23LC1024 | PCF8574T | 1024 | 2 |

The designer reports the SRAM fitted varies between builds but is **usually a 23LC512 (64 KB)**, which matches the attached `SRAM_TYPE 512` build. The BoM's 23LC1024 needs `SRAM_TYPE 1024`. Check the chip on the board before flashing.

### 6.2 Main sequence (`loop()`)
1. **`restartCPU()`** (red very fast). For 2 s it watches `RESX` as an input. If `RESX` goes high in that window, another programmer is resetting the target, so this one **disables itself**: both LEDs off, infinite loop, all port D pins left as inputs (status 7, "disable v101-programmer"). PR1's start-up pulse (RESX high 500 ms) falls inside that window, so if both are fitted and powered together, PR1 takes over and PR2 goes passive. Otherwise it pulses `RESX` high for 200 ms, releases it, and goes to slow red.
2. **Receive** (`readCode()`). Bytes go to SRAM until the last three are `XXX` (0x58 ×3). Blue slow once data starts. **No timeout** (PR1 gives up after 1 s of silence).
3. **Echo** (`verifyCode()`). 1 s pause, then SRAM[0], [10], [20] … with 500 µs spacing. Both LEDs fast.
4. **Verdict.** `v` → go. Anything else → leave `loop()` and run `restartCPU()` again (2.2 s).
5. **`takeBus()`.** Preset ROMCSX low, ROMWEX high, ROMOEX low, RESX low, then make PD2/3/5/6/7 outputs, assert BUSRQ low, pulse RESX high 200 ms. No BUSAK check (none on the bus).
6. **`burnRom()`** (both slow). Byte mode for every byte (section 6.4). `u` every 2 %, `U` at the end. A DATA-poll timeout sends `T` and aborts (section 8, item 4).
7. 200 ms pause, then **`verifyRom()`**: each byte is read back up to 1000 times, 1 ms apart, until it matches. `g` every 2 %, then `p` (solid blue) or `f` (fast red), held for 3 s.
8. **`releaseBus()`.** ROMOEX low, all three PCF8574s to `FFh` (weak-high inputs), BUSRQ high, RESX high 500 ms then low. Port D is **left as outputs**, driving the idle levels (section 8, item 6). Back to step 2 without repeating `restartCPU()`.

Note `verifyRom()` returns **1 on failure, 0 on success**; the caller is consistent with this.

### 6.3 LED codes (Timer1 compare ISR)
Timer1 prescaler /64 (`TCCR1B = 0b011`; the comment saying /128 is wrong), compare 31 250 → 125 ms base period, as on PR1.

| `status` | Red (PB0) | Blue (PB1) | State |
|---|---|---|---|
| 0 | slow flash | off | Waiting for host |
| 1 | off | slow flash | Receiving |
| 2 | fast (÷3) | fast (÷3), alternating with red | Echo transfer |
| 3 | slow | slow, alternating with red | Burning / verifying ROM |
| 4 | fast (÷4) | off | Verify failed (the comment says "solid red"; it flashes) |
| 5 | off | solid | Success |
| 6 | very fast (÷6) | unchanged | Start-up reset, or write timeout |
| 7 | off | off | Disabled (another programmer present) |

### 6.4 Bus cycles through the expanders
**Read** (`readFromROM`, used for DATA polling and verify): DATA ← `FF` and a dummy read, ROMCSX high, ADHI ← A8–A14 (A15 forced 0), ADLO ← A0–A7, 2 µs, ROMOEX low, 2 µs, read DATA, ROMOEX high, ROMCSX low. **5 I²C transactions.**

**Byte write** (`writeByte`): ROMOEX high, DATA ← `FF` and a dummy read, ROMCSX high, ADHI, ADLO, DATA ← byte, 1 µs, ROMWEX low 1 µs, ROMWEX high, ROMOEX low, ROMCSX low, dummy read; then `waitForCycle()` DATA-polls with repeated reads until the byte reads back (500 ms timeout). **6 I²C transactions** plus the polling.

**Page write** (`writePage`): sets ADHI once, then for 64 bytes 2 transactions each (ADLO, DATA), pulsing ROMCSX and ROMWEX together. Present but **not called**.

### 6.5 Why it is slow
- `setup()` calls `Wire.setClock(400000)` **before** `Wire.begin()`. In the standard AVR Wire library `begin()` re-initialises the TWI at the default 100 kHz, so the bus very likely runs at **100 kHz**, not 400 kHz. *To confirm with a scope on SCL.* (100 kHz is also the PCF8574's rated maximum, so this accident keeps it in spec.)
- At 100 kHz a 2-byte I²C transaction takes roughly 0.2–0.25 ms. So, approximately:
  - each write ≈ 1.5 ms of I²C traffic, plus the EEPROM's own byte-write cycle (AT28C256 t<sub>WC</sub> up to 10 ms), detected by polls of ≈ 1.1 ms each;
  - a full 32 KB ROM therefore takes several minutes to burn, plus about 35–40 s to verify. *Figures are estimates.* The designer hasn't timed a full upload ("too long, but it works — just very slow").
- **Page mode can't work here** (confirmed by the designer: the I²C-limited ATmega8 can't feed bytes fast enough before the EEPROM's page window times out; moving to the ATmega64A on PR1, which drives the bus directly, made 28C256 page mode possible): an AT28C256 page needs each byte within 150 µs of the last (t<sub>BLC</sub>), but each page byte costs two I²C transactions (≈ 0.45 ms at 100 kHz, still ≈ 0.12–0.15 ms at a true 400 kHz). That is why the page routine is unused and why PR1 moved the bus onto the MCU's own ports.

### 6.6 Serial protocol
Identical bytes to PR1 (`XXX` EOF, echo every 10th byte, `v`/`b`, `u`/`U`, `T`, `g`, `p`/`f`), which is why `uploadROM.py` works unchanged. Differences: 500 µs echo spacing (PR1 50 µs), a 1 s pause before the echo, and no receive timeout.

---

## 7. PLD interaction (CPU boards)

No PLD on this board. The lines it drives behave on each CPU board as already documented:

| CPU board | ROMCSX | RESX | ROMOEX / ROMWEX | BUSRQ |
|---|---|---|---|---|
| Z80 SBC (`v102-z80-00`) | `!CSB0 = … # ROMCSX` (1 k pull-down) | `!RSTB = RESX # !RESB` | ROM pins direct | Z80 /BUSRQ |
| 6502 SBC (`v102-6502-00`) | forces ROM, masks RAM/VIA (not IORQB) | via IC6A diode-OR | ROM pins direct | 65C02 `BE` |
| MTX (`v102-mtx-2`) | forces main ROM or ROMx via SW3 (no pull-down) | via IC9 | both ROMs direct | Z80 /BUSRQ |

Because PR2 forces A15 = 0, the image is limited to 32 KB, which covers all three boards (28C256 or smaller). The 6502 board's I/O-window issue during programming (6502 document, section 4.9) applies here too, and lasts longer because each byte takes milliseconds.

---

## 8. Observations and things to watch

Most important first.

1. **MTX data pull-downs vs PCF8574 weak highs.** The MTX board's 4k7 data pull-downs hold any PCF8574 `1` near 0.5 V, so the EEPROM probably latches `0` in those bits. Verify would report `f`. PR2 hasn't been used on the MTX board (PR1 is the MTX programmer), so this is untested; the cure is a stronger high (a driver such as a 74HCT245 on the DATA expander) or weaker pull-downs on the MTX board.
2. **Firmware build must match the fitted SRAM.** Builds vary (usually 23LC512, as in the attached `SRAM_TYPE 512` file). A board with a 23LC1024 needs the 1024 build, or 16-bit addressing gives garbage and every echo check fails. Keep one source with a per-board config, or detect the SRAM size at start-up.
3. **Two programmers → two "Z80" serial ports.** If PR1 is stacked on a pad and both USB cables are connected, `uploadROM.py` finds two matching ports and aborts. The RESX self-disable keeps PR2 off the bus, but not off USB. Connect only one USB cable, or give PR2's FT232 a different serial string.
4. **Write timeout leaves the bus held.** On `T`, `loop()` exits without `releaseBus()`: BUSRQ stays low and the expanders keep driving. The target stays halted until power is cycled or another upload completes. Call `releaseBus()` before breaking out.
5. **I²C clock order.** `Wire.setClock()` must come after `Wire.begin()` to take effect (6.5). The PCF8574 is only rated to 100 kHz, so real speed needs a faster expander (e.g. the 1 MHz [PCA9674](https://www.nxp.com/docs/en/data-sheet/PCA9674_PCA9674A.pdf)) or direct port drive, as on PR1.
6. **Control lines left driven after release.** Port D stays push-pull after `releaseBus()` (ROMCSX low, ROMWEX high, ROMOEX low, BUSRQ high, RESX low). These match the CPU boards' pull states, so it's harmless alone, but a second programmer on the bus would fight it. Return them to inputs as PR1 does.
7. **12 V on `PWR` reaches more places.** `PWR` is now on PROG pin 8 at three pads and on ICPP pin 2 at three pads, where it sits between GND (pin 1) and **A8 (pin 3)**. A one-pin offset on an ICPP plug puts 12 V onto an address line. If both J1 and the CPU board's own jack are plugged in, two adaptors are paralleled on `PWR`.
8. **ICSP powers the whole stack.** J6 pin 5 is wired straight to +5 V with no jumper, so a powered ISP tool back-feeds every board on all three pads.
9. **BOD at 2.7 V with a 16 MHz clock.** The ATmega8 is only rated for 16 MHz at ≥ 4.5 V. BODLEVEL = 0 (4.0 V) is safer. Same point as PR1.
10. **EOF marker in data.** As on PR1, any `XXX` in the binary ends reception early; with no receive timeout the leftover bytes are then taken as the echo verdict.
11. **No SDP handling.** An EEPROM with software data protection enabled gives `T` on the first byte.
12. **Minor firmware points:**
    - `restartCPU()` stores `millis()` in a 16-bit `unsigned int`. After about 65 s of uptime the 2 s window and the disable check are skipped. Use `unsigned long`.
    - `readFromPCF()` returns an uninitialised byte if the expander doesn't answer.
    - Unused globals (`dumpind`, `select`, `counter`, `testit`, `time`) and the `LiquidCrystal_I2C` include can go.
13. **I²C pull-ups of 1 k** sink 5 mA, above the PCF8574's 3 mA V<sub>OL</sub> rating. It works on a short bus; 2k2–4k7 would be within spec.
14. **Decoupling:** no capacitor right at IC1. Add 100 nF at each IC in any respin.
15. **Housekeeping:** the folder holds `PHONO-SRC-00A-erc.rpt` (name from another project), `untitled.kicad_sch`, two `.kicad_pro` files (`V102-PR2-0.kicad_pro` and `V102-PR2-0-Nigel.kicad_pro`) and stale KiCad lock files (`~*.lck`). Schematic note says "BYPASS DIODES" for the 1 µF capacitors.

---

## 9. Open questions

- Actual SCL frequency (100 kHz expected, section 6.5).
- MTX compatibility is untested (item 1); keep PR1 for the MTX board.

Resolved: SRAM varies by build, usually 23LC512; 90° rows + ICPP = v101 interface; full-ROM time not measured but "works, just very slow"; page mode abandoned because of the I²C speed limit (fixed on PR1 with the ATmega64A).
