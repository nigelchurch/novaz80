# NOVAZ80 ROM Programmer — V102-PR1-2 (Rev 002)

Design analysis from `V102-PR1-2.net` (KiCad/Eeschema 9.0.7 export, 2026-11-25), the schematic PDF, the BoM, the MCU firmware `z80_isp_fast.cpp`, the host script `uploadROM.py` and the assemble/burn batch file.

Title block: *NOVAZ80 Project – v102-PR1*, NOVA Embedded Solutions, drawn 2023-09-01, Rev 002.
Revision notes:
1. Changed to ATmega64A; MCU drives the ADDR and DATA lines directly (no buffers).
2. Added JTAG and a power input for a stand-alone dev-board option.
3. Corrected SPI programming connections (MISO/MOSI → PDO/PDI).

---

## 0. Where this board sits in the NOVAZ80 project

NOVAZ80 is a family of square, identically sized boards that **stack**. Each board has the same bus connectors in its four corners, so the address bus, data bus, control bus and power pass from the bottom of the stack to the top. Any order works electrically. The only limits are physical (a tall component on one board clashing with the board above).

| Board | Role |
|---|---|
| **Z80 SBC** | Z80 CPU, RAM, ROM (normally 28C256), PLD glue logic |
| **6502 SBC** | Alternative CPU board: 32 K RAM / 32 K ROM, PLD glue. Uses the same bus, so it works with the same I/O and VDP boards |
| **MTX board** | Alternative to the SBCs. With the I/O and VDP boards it makes a hardware-equivalent **Memotech MTX512** with the original ROM/RAM paging, running the original BIOS, ROMs and games. Previously under-used ROM areas are used for extensions. Smaller 28-series EEPROMs |
| **I/O board** (optional) | Peripheral I/O shared by all three CPU boards |
| **VDP + sound board** (optional) | TMS99xx-family video and a sound chip, shared by all three CPU boards |
| **Programmer (this board)** | Burns the CPU board's ROM in circuit from the PC, through the stack bus |

A key point of the architecture is that the **same I/O and VDP boards serve both the Z80 and the 6502**, with each CPU board's PLD translating its CPU's bus onto the common one. The programmer relies on the same idea: it reaches the ROM through generic `ROMCSX / ROMWEX / ROMOEX / BUSRQ / RESX` lines that each CPU board's PLD interprets.

Each board gets its own document like this one. Details of the CPU boards (PLD equations, memory maps, MTX paging) are in their own write-ups and are referenced here only where the programmer depends on them.

Status: V102-PR1-2 has been **built and tested and is in use**. A future revision (4-layer, ground planes in the middle of the stack-up for signal integrity) is planned. Section 8 lists points to consider for that revision.

---

## 1. Purpose

A plug-in card for the Z80 (and 6502) SBCs that burns the system EEPROM **in circuit**:

1. The host PC assembles the source (vasm), then `uploadROM.py` streams the binary over USB-serial.
2. The ATmega64A stores it in a 64 KB SPI SRAM (23LC512) and echoes every 10th byte back for the host to check.
3. Once the host replies `v`, the MCU requests the target bus (`BUSRQ`), holds the target CPU off, and drives A0–A15, D0–D7 and the ROM control lines directly to write the EEPROM (64-byte page mode).
4. It reads the ROM back against the SRAM, reports pass/fail, releases the bus and resets the target so the new code runs.

---

## 2. Block diagram

```
          USB mini-B (J7)
               │ D+/D-            VBUS ─R8 4k7─┬─R7 10k─ GND
               ▼                               │
        ┌─────────────┐  RESET# ◄─────────────┘ (FTDI held in reset when USB unplugged)
        │  FT232RL    │
        │  IC2 (5V IO)│ TXD ──► PE0/RXD0 ─┐
        │             │ RXD ◄── PE1/TXD0 ─┤ (also PDI/PDO for ISP, J6)
        │             │ DTR ──SW1──C3 100n──► RESET (Arduino-style auto-reset, switchable)
        └─────────────┘
                                   ┌───────────────────────────┐
  16 MHz Y1 ──────────────────────►│        ATmega64A IC1      │
                                   │  PA0-7 ───────────────────┼──► A0–A7   (J1/J111)
  23LC512 IC3 ◄── SPI (PB0-PB3) ──►│  PC0-7 ───────────────────┼──► A8–A15  (J11, J5)
  (64 KB SRAM buffer)              │  PD0-7 ◄──────────────────┼──► D0–D7   (J4/J444)
                                   │  PE2 ROMCSX  PE3 ROMWEX   │
                                   │  PE5 ROMOEX  PE6 BUSRQ    ├──► PROG (J22), ICPP (J5)
                                   │  PE7 RESX                 │
                                   │  PF0 RED  PF1 BLUE        ├──► LEDs D3, D2
                                   │  PF4-7 JTAG               ├──► J8
                                   └───────────────────────────┘
  Barrel jack J9 ─► AMS1117-5.0 ─► +5V ◄─► target bus +5V (J2/J222 pin 2), J12
```

---

## 3. Parts (BoM)

| Ref | Part | Function | Datasheet |
|---|---|---|---|
| IC1 | ATmega64A, TQFP-64 | Controller | [ATmega64A](https://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-8160-8-bit-AVR-microcontroller-ATmega64A_datasheet.pdf) |
| IC2 | FT232RL, SSOP-28 | USB ↔ UART | [FT232R](https://ftdichip.com/wp-content/uploads/2020/08/DS_FT232R.pdf) |
| IC3 | 23LC512, SOIC-8 | 64 KB SPI SRAM image buffer | [23LC512](https://ww1.microchip.com/downloads/en/DeviceDoc/20005155B.pdf) |
| IC4 | AMS1117-5.0, SOT-223 | 5 V LDO for barrel-jack power | [AMS1117](http://www.advanced-monolithic.com/pdf/ds1117.pdf) |
| Y1, C1, C2 | 16 MHz HC49-SD + 2× 22 pF | MCU clock | — |
| C3 | 100 nF | DTR auto-reset coupling cap | — |
| C4–C8 | 1 µF | +5 V bypass (C5–C8 "adjacent to ICs"), C4 = LDO output | — |
| C9 | 100 nF | FT232 3V3OUT decoupling | — |
| C10 | 1 µF | LDO input | — |
| D1 / R1 | Green LED / 470 R | Power indicator (+5 V) | — |
| D2 / R3 | Blue LED / 470 R | Status (PF1) | — |
| D3 / R4 | Red LED / 470 R | Status (PF0) | — |
| R2 | 10 k | MCU RESET pull-up | — |
| R5 | 1 k | SRAM /CS pull-up (SRAM deselected while MCU resets) | — |
| R6 | 1 k | SRAM SIO2 pull-up | — |
| R7, R8 | 10 k / 4k7 | VBUS sense divider → FT232 RESET# (≈3.4 V when USB present) | — |
| SW1 | SPDT slide | Enables/disables DTR auto-reset | — |
| JP1 | 2-pin jumper | Connects +5 V to ICSP J6 pin 5 | — |
| J1–J44 etc. | 8-way pin sockets ("11 mm") | Target-bus stacking connectors (section 5) | — |
| J5 | 1×15 header "ICPP" | Upper address + control + power to a cabled target | — |
| J6 | 2×3 IDC (horizontal) "ICSP" | AVR SPI programming of IC1 | — |
| J7 | USB mini-B | Host link | — |
| J8 | 2×5 IDC "JTAG" | AVR JTAG debug | — |
| J9 | Barrel jack (Würth 694106301002) | Stand-alone power input | — |
| J10 | 1-pin | RESET test point / "option" | — |
| J12 | 2×3 socket | +5 V / GND only (pins 2/4/6 = +5 V, 1/3/5 = GND) | — |

The target ROM is not on this board. The firmware assumes an AT28C256-type EEPROM: 64-byte pages, ≤150 µs between bytes in a page, DATA polling for end-of-write ([AT28C256](https://ww1.microchip.com/downloads/en/DeviceDoc/doc0006.pdf)).

---

## 4. Subsystems

### 4.1 Microcontroller (IC1, ATmega64A)
- 16 MHz crystal on XTAL1/XTAL2 with 22 pF loads.
- RESET: 10 k pull-up (R2). Also goes to ICSP J6-2, test pin J10, and through C3 → SW1 → FT232 DTR.
- VCC, AVCC and AREF all tie straight to +5 V. The ADC isn't used.
- /PEN left open (it has an internal pull-up).
- **Fuses** (noted on the schematic): LF 0xBF, HF 0x0E, LB 0xFF. Decoded:
  - LF 0xBF → CKSEL = 1111, SUT = 11 (external crystal, slow-rising power), **BODEN programmed**, BODLEVEL = 1 (**2.7 V**).
  - HF 0x0E → OCDEN and JTAGEN programmed (JTAG enabled on PF4–PF7), SPIEN programmed, CKOPT programmed (full-swing oscillator, needed at 16 MHz), EESAVE off, BOOTSZ = 11 (512-word boot section), **BOOTRST programmed** (reset jumps to a bootloader).
  - LB 0xFF → no lock bits.
- BOOTRST combined with the DTR auto-reset shows the firmware is normally uploaded over USB through a serial bootloader (MegaCore-style). ICSP and JTAG are the fallbacks.

### 4.2 USB-serial (IC2, FT232RL)
- **Self-powered configuration.** FT232 VCC and VCCIO are on the board's +5 V rail, not on USB VBUS. VBUS feeds only the R8/R7 divider into RESET#, so the FTDI chip stays in reset (UART pins high-Z) whenever USB is unplugged. A note on the schematic uses this on purpose: **unplug USB while ISP-programming the MCU**, because FT232 TXD shares PE0 (= PDI) and RXD shares PE1 (= PDO). There are no series resistors on these lines.
- **USB does not power the board.** Power must come from the target bus, J12 or the barrel jack.
- TXD → PE0 (RXD0), RXD ← PE1 (TXD0). 5 V logic (VCCIO = 5 V).
- DTR → SW1 → C3 → RESET gives auto-reset when SW1 is closed. SW1 therefore selects **uploading mode** (normal, no auto-reset) or **programmer-firmware mode** (auto-reset for the bootloader). RTS, CTS and the other modem lines are unused.
- CBUS0–4 are unused, so there are no TX/RX activity LEDs. CBUS0/1 default to TXLED#/RXLED# if you ever want them.
- The 3V3OUT pin is decoupled only (C9). TEST, AGND and GND are grounded. USB ID (J7-4) is grounded.
- The host script finds the programmer by looking for **"Z80" in the FT232's USB serial number**, which has been customised in the FTDI EEPROM (FT_Prog).

### 4.3 Image buffer (IC3, 23LC512)
- Hardware SPI: SCK = PB1, MOSI = PB2 → SI, MISO = PB3 ← SO, /CS = PB0 (/SS) with a 1 k pull-up.
- /HOLD is tied to +5 V and SIO2 is pulled up by R6, so it runs in plain SPI mode.
- In firmware `SRAM_23LC SRAM(&SPI, 8, SRAM_23LC512)`: Arduino pin 8 is PB0 in the MegaCore ATmega64 pin map, which matches the hardware.
- The SPI bus also appears on **J44 AUX** (pins 3/4/5 = MISO/MOSI/SCK).
- Capacity is 64 KB, so the largest image is 65 533 bytes (64 K minus the 3-byte EOF marker).

### 4.4 Power
Three ways onto the single +5 V net:
1. **From the target SBC** through the SPEC connectors (J2/J222 pin 2 = +5 V, pin 1 = GND). This is the normal case when stacked.
2. **J12** 2×3 power socket.
3. **J9 barrel jack → AMS1117-5.0** (stand-alone/dev-board option). It needs roughly ≥ 6.5 V in. The jack's switch contact is tied to GND, so it isn't used as a switch.

### 4.5 Indicators

| LED | Drive | Meaning |
|---|---|---|
| D1 green | +5 V via 470 R | Power |
| D3 red | PF0 via 470 R | Status (see 6.3) |
| D2 blue | PF1 via 470 R | Status (see 6.3) |

### 4.6 MCU programming / debug headers
- **J6 ICSP (2×3, horizontal IDC):** 1 GND, 2 RST, 3 PDI (PE0), 4 SCK (PB1), 5 +5 V via JP1, 6 PDO (PE1).
  This is the standard Atmel 6-pin ISP pinout with the pin numbers mirrored (pin *n* ↔ 7−*n*): standard is 1 MISO, 2 VCC, 3 SCK, 4 MOSI, 5 RST, 6 GND. It's probably deliberate, to suit the horizontal footprint, but check the key/cable orientation before use. On the ATmega64A, ISP uses **PDI/PDO on PE0/PE1**, not the SPI MOSI/MISO pins (that was revision note 3). JP1 decides whether the ISP tool powers the board.
- **J8 JTAG (2×5):** 1 +5 V, 2 TMS (PF5), 3/5/7/9 GND, 4 TCK (PF4), 6 TDO (PF6), 8 TDI (PF7), 10 n/c.
  This is **not** the standard Atmel 10-pin JTAG pinout (TCK/GND/TDO/VTref/TMS/nSRST/–/nTRST/TDI/GND), and it carries no nSRST. An Atmel-ICE or similar needs an adapter.

---

## 5. Target-bus connectors

All are 8-way "11 mm" pin sockets (long-pin stacking type), placed on the bottom side in four corner clusters. The PCB places them as follows:

| Corner | Connectors |
|---|---|
| Top-left | J1 ADDR, J11 ADDR2, J111 ADDR |
| Top-right | J2 SPEC, J22 PROG, J222 SPEC |
| Bottom-left | J4 DATA, J44 AUX, J444 DATA |
| Bottom-right | J3 CTRL, J33 MTX, J333 CTRL |

In each corner, the first two connectors listed are parallel rows 2.54 mm apart. The third (J111, J222, J333, J444) runs at 90° to them and duplicates the first one pin for pin.

**Stacking (as described by the designer):** the duplicated pairs carry each bus group up to the board above and down to the board below. *To confirm against the PCB/3D model:* long-pin stacking sockets usually pass signals through a single footprint (socket on top, pins below). The single connectors (J11 A8–A15, J22 PROG, J33 MTX, J44 AUX) also need to reach both neighbours if the programmer can sit anywhere in the stack.

| Conn | Name | Pins 1→8 | Connected to MCU? |
|---|---|---|---|
| J1 / J111 | ADDR | A0 A1 A2 A3 A4 A5 A6 A7 | Yes, PA0–PA7 |
| J11 | ADDR2 | **A15** A14 A13 A12 A11 A10 A9 **A8** (reversed order) | Yes, PC7…PC0 |
| J4 / J444 | DATA | D0 … D7 | Yes, PD0–PD7 |
| J22 | PROG | n/c, ROM7, BUSRQ, ROMWEX, ROMCSX, RESX, ROMOEX, PWR | BUSRQ=PE6, ROMWEX=PE3, ROMCSX=PE2, RESX=PE7, ROMOEX=PE5 |
| J2 / J222 | SPEC | GND, +5V, VDPINTB, IEO1, IEO2, 4M, OUT0, KBDRST | Power only, rest pass-through |
| J3 / J333 | CTRL | RSTB, CLK, M1B, MREQB, IORQB, RDB, WRB, INTB | No, pass-through |
| J33 | MTX | P0 P1 P2 P3 R0 R1 R2 CPM | No (each pin is a one-node net, so mechanical/locating only) |
| J44 | AUX | –, –, MISO, MOSI, SCK, –, –, – | SPI bus |

**J5 ICPP (1×15):** 1 GND, 2 PWR, 3–10 A8–A15, 11 BUSRQ, 12 ROMWEX, 13 ROMCSX, 14 RESX, 15 ROMOEX.
The designer describes J5 as the header used for the one-time programming of the programmer board itself. Programming the programmer is outside the scope of this document. *To confirm:* in the netlist J5 carries A8–A15 and the ROM/bus control lines, not the AVR ISP signals. The ATmega64A's ISP signals (RST, SCK, PDI, PDO) are on **J6**. J5 also lacks A0–A7 and D0–D7.

Single-node nets with no other connection on this board: ROM7 (J22-2), the J33 signals, and PWR (J22-8 ↔ J5-2 only, not +5 V).

The ROM control polarities (ROMCSX active-high, ROMWEX/ROMOEX active-low, RESX active-high) are decoded by the **PLD on the target SBC**, which isn't part of this design. Check them against the PLD equations.

### MCU pin allocation summary

| Port | Use |
|---|---|
| PA0–7 | A0–A7 |
| PB0–3 | SRAM /CS, SCK, MOSI, MISO |
| PB4–7 | unused |
| PC0–7 | A8–A15 |
| PD0–7 | D0–D7 (bidirectional) |
| PE0/PE1 | UART0 RX/TX (FT232), also ISP PDI/PDO |
| PE2/3/5/6/7 | ROMCSX, ROMWEX, ROMOEX, BUSRQ, RESX |
| PE4 | unused |
| PF0/PF1 | Red / blue LED |
| PF2/PF3 | unused |
| PF4–7 | JTAG |
| PG0–4 | unused |

All target-facing pins sit at AVR reset default (inputs, hi-Z) until the firmware takes the bus, so the card is passive while the SBC runs.

---

## 6. Firmware (`z80_isp_fast.cpp`)

Arduino framework, MegaCore-style ATmega64 core. Build switches:

| Define | Value | Meaning |
|---|---|---|
| `SRAM_TYPE` | 512 | 23LC512 (64 KB) |
| `PAGEMODE` | 1 | 64-byte page writes |
| `BAUD_RATE` | 57600 | Must match `uploadROM.py` |
| `VERIFY_STEP` | 10 | Echo every 10th byte for transfer check |
| `T_*` | 1 µs | Read/write setup and hold |

### 6.1 Main sequence (`loop()`)
1. **Reset the target** (red LED very fast). RESX high 500 ms → low, wait 2 s, then high 200 ms → low. RESX is then released to input. This takes about **3.2 s**.
2. **Receive.** Each serial byte goes into SRAM at `index++`. Reception ends when the last three stored bytes are `88,88,88` (`"XXX"`, the EOF frame). The LED changes from slow red to slow blue once bytes arrive. If the host goes quiet for 1 s mid-transfer, it gives up.
3. **Echo check.** `datalength = index − 3`. It sends SRAM[0], SRAM[10], SRAM[20] … at 50 µs spacing, then waits `datalength/16` ms. Both LEDs flash fast.
4. **Wait for the host verdict.** `v` means go. Anything else aborts.
5. **Take the bus.** BUSRQ is asserted (PE6 low), ROMCSX high, ROMWEX high, ROMOEX low. The target is pulsed through RESX for 200 ms. A/C/D ports become outputs. **BUSAK is not monitored** (it isn't on any connector). The firmware just waits 200 ms.
6. **Burn** (both LEDs slow). For each full 64-byte page `writePagetoROM()`: set A8–A15 once, raise OE, then for 64 bytes set A0–A7 + data and give a 1 µs WE pulse, then **DATA-poll** the page's last byte until it reads back correctly (500 ms timeout → `T`). The remaining bytes use `writeBytetoROM()`, one byte at a time with the same polling. It sends `u` every 2 % and `U` when done.
7. **Read-back verify.** Every byte is compared ROM vs SRAM. It sends `g` every 2 %, then `p` on pass (solid blue) or `f` on fail (fast red).
8. **Release.** Ports go to inputs, ROMCSX low, BUSRQ released, target reset via RESX for 500 ms, then all of PORTE goes hi-Z. It returns to step 2 and waits for the next file. It does not repeat the 3.2 s reset unless it exits via timeout or abort.

### 6.2 Serial protocol

| Direction | Byte(s) | Meaning |
|---|---|---|
| Host → MCU | raw binary, then `X X X` (0x58 ×3) | Image + EOF |
| MCU → Host | every 10th byte | Transfer echo |
| Host → MCU | `v` / `b` | Echo good / bad |
| MCU → Host | `u` … `U` | Burn progress (2 %) / burn done |
| MCU → Host | `T` | EEPROM write timeout |
| MCU → Host | `g` … | Verify progress (2 %) |
| MCU → Host | `p` / `f` | ROM verify pass / fail |

### 6.3 LED codes (Timer1 compare ISR)

| `status` | Red (PF0) | Blue (PF1) | State |
|---|---|---|---|
| 0 | slow flash | off | Waiting for host |
| 1 | off | slow flash | Receiving |
| 2 | fast (3×) | fast (3×) | Echo/verify transfer |
| 3 | slow | slow | Burning ROM |
| 4 | 4× flash | off | ROM verify failed |
| 5 | off | solid | Success |
| 6 | 6× flash | off | Target reset / write timeout |

Timer1 uses prescaler /64 (`TCCR1B = 0b011`; the comment saying /128 is wrong). 16 MHz / 64 / 31250 gives a 125 ms ISR period, so the base flash is 4 Hz toggling (about 2 Hz blink).

---

## 7. Host side

### 7.1 Batch file flow
1. Detect which PC it's on and set `%realpath%`.
2. `vasmz80_oldstyle -Fbin -dotdir … z80.asm -L listing.txt -nocase -o …\z80.out` (the 6502 variant swaps in `vasm6502_oldstyle`).
3. On success: move `z80.out` into `z80-current\`, make a hex dump (`certutil` → `hexdump_mod.py`) and a formatted listing (`listing.py`).
4. `python uploadROM.py ./z80-current/z80.out` (the burn).
5. Rename/copy the output to `z80.hex` and `z80.obj`.

`-Fbin` output starts at file offset 0, so it is always burnt from **ROM address 0**. The program's `ORG` must correspond to wherever the PLD maps ROM address 0 into CPU space (e.g. `$8000` on a 32 K-ROM 6502 map).

### 7.2 `uploadROM.py`
1. Enumerate COM ports, skip COM1, and pick the one whose USB serial number contains "Z80". It aborts if there are zero or more than one.
2. Open at 57600 8N1 with a 2 s timeout (3 retries), then pause about 1.5 s.
3. Send the binary one byte per `write()` call, then `X X X`.
4. Read one echo byte per 10 bytes and compare. Send `v` or `b`.
5. Listen for `u/U/g/T/p/f` and draw progress bars. Print the elapsed time.

---

## 8. Observations and things to watch

Most important first.

1. **EOF marker can occur in real data.** The firmware stops receiving at *any* three consecutive 0x58 bytes. A binary containing `XXX` (text, tables, graphics) gets truncated. Usually the host's echo check then fails, but the leftover bytes sit in the MCU's RX buffer and the first one is read as the host's verdict. If that byte happens to be `v` (0x76), a truncated image would be burnt. A length prefix or escape scheme would remove this.
2. **SW1 modes (confirmed by the designer):** *uploading mode* (normal; DTR auto-reset off) and *programmer-firmware mode* (DTR auto-reset on, for the bootloader). Leave it in uploading mode for ROM burns. With auto-reset on, opening the port restarts the MCU: bootloader delay plus the ~3.2 s target-reset sequence. The script starts sending after about 1.5 s, which overflows the 64-byte RX buffer. The same 3.2 s window applies if a new upload starts right after an aborted one.
3. **No BUSAK feedback.** Bus ownership is assumed after a fixed 200 ms. The MCU drives A0–A15 and D0–D7 with **no series resistors or buffers** (revision note 1), so if the CPU hasn't released the bus (or a 6502 board doesn't honour BUSRQ via its PLD), you get direct output contention.
4. **FT232 ↔ ISP sharing PE0/PE1.** As the schematic note says, unplug USB while ISP-programming the MCU. Small series resistors (≈1 k) on TXD/RXD would make this tolerant.
5. **Non-standard connector pinouts.** J6 ICSP is mirrored and J8 JTAG is custom (section 4.6). Label them on the silkscreen or make adapters.
6. **BOD at 2.7 V with a 16 MHz clock.** The ATmega64A is only rated for 16 MHz at ≥ 4.5 V. BODLEVEL = 0 (4.0 V) would be the safer fuse setting. OCDEN is also programmed, which the datasheet advises against outside debugging (extra current, oscillator stays on).
7. **USB alone won't power the card.** You need the SBC, J12 or the barrel jack (≥ about 6.5 V for the AMS1117). If the barrel jack and the target both supply +5 V at the same time, two supplies are paralleled on one rail.
8. **EEPROM Software Data Protection (SDP) isn't handled.** If an EEPROM has had SDP enabled (some standalone programmers do this), writes are ignored and the firmware reports `T`. Adding the SDP-disable sequence would cover it.
9. **ROM control polarities depend on the target PLD.** The firmware comments are inconsistent (e.g. ROMOEX called both "active low" and "high impedance" when driven low). Verify against the PLD equations for each SBC.
10. **Minor firmware points:**
    - The receive loop starts by reading SRAM at `index−3` with `index = 0` (uint32 underflow → reads 0xFFFD–0xFFFF). That's harmless unless stale `XXX` sits at the top of SRAM.
    - The verify loop uses a `float` counter, which is slow but correct up to 64 K.
    - `#include <SRAM_23LC.h>` and MegaCore pin 8 = PB0 must stay paired if the core changes.
    - The host sends one byte per `write()` and redraws the progress bar each time. Sending in chunks would make the transfer much faster.
