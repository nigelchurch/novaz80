"""Generates boards/*.html from tools/content. Run: python tools/build.py
index.html is hand-written and is not touched."""
import html
import json
import os
import re
from markdown_it import MarkdownIt
import diagrams

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = os.path.join(ROOT, "tools", "content")
E = html.escape


def read(p):
    with open(p, encoding="utf8", errors="replace") as f:
        return f.read()


DATA = json.loads(read(os.path.join(C, "boards.json")))

META = {
    "z80": ("Z80 SBC", "A complete minimal computer on one board, and the base of every Z80 stack.",
            [("CPU", "Z80 at 4 MHz"), ("ROM", "32 K EEPROM, 0000–7FFF"), ("RAM", "32 K SRAM, 8000–FFFF"), ("I/O", "CTC at 18h, PIO at 20h"), ("Glue", "ATF16V8B")]),
    "6502": ("6502 SBC", "A 6502 that speaks the Z80 bus well enough to share its I/O and video boards.",
             [("CPU", "W65C02S at 1 MHz"), ("ROM", "32 K EEPROM, 8000–FFFF"), ("RAM", "0000–7EFF"), ("I/O", "VIA at 7FF0, bus window at 7F00"), ("Glue", "ATF20V8B")]),
    "mtx": ("MTX512 CPU board", "The Memotech's paged memory, rebuilt so that the original software runs.",
            [("CPU", "Z80, clocked by the video board"), ("ROM", "32 K as four 8 K blocks, plus optional ROMx"), ("RAM", "64 K as two 32 K SRAMs"), ("Paging", "74AHC273 register at port 00h"), ("Needs", "I/O and video + sound boards")]),
    "io1": ("I/O board", "Serial, timers, parallel ports and two kinds of keyboard, shared by all three machines.",
            [("Serial", "Z80 SIO at 0Ch, over USB or DB9"), ("Timers", "Z80 CTC at 08h"), ("Parallel", "Z80 PIO at 10h"), ("Keyboard", "PS/2 or MTX matrix"), ("Glue", "GAL16V8")]),
    "vdp": ("Video + sound", "The MTX's video and sound chips, with static RAM where the obsolete DRAM used to be.",
            [("Video", "TMS9929A or TMS9918A"), ("VRAM", "16 K, in a 62256 SRAM"), ("Sound", "SN76489"), ("Out", "Component or composite video, audio"), ("Glue", "GAL16V8")]),
    "io2": ("I/O 2 with LCD", "A front panel for the top of the stack: four lines of text, eight buttons, two spare ports.",
            [("Display", "20 × 4 HD44780 at 30h"), ("Ports", "82C55A at 24h"), ("Buttons", "Eight"), ("Position", "Top of the stack"), ("Glue", "GAL16V8")]),
    "pr1": ("Fast programmer", "Takes over the bus and writes the CPU board's ROM where it sits.",
            [("Controller", "ATmega64A at 16 MHz"), ("Buffer", "64 K SPI SRAM"), ("Link", "USB, through an FT232RL"), ("Writes", "64-byte pages"), ("Targets", "All three CPU boards")]),
    "pr2": ("3-pad programmer", "The first programmer to work, and a side-by-side bench for debugging every board.",
            [("Controller", "ATmega8"), ("Bus drive", "Three PCF8574 I²C expanders"), ("Writes", "One byte at a time"), ("Pads", "Three, all wired in parallel"), ("Accepts", "v101 and v102 boards")]),
}
SHEETS = {"z80": ["Main sheet", "Connectors"], "6502": ["Main sheet", "Connectors"], "vdp": ["Main sheet", "Connectors"], "pr2": ["Main sheet", "v102 bus"]}
PLD = {"z80": "V102-Z80-00", "6502": "V102-6502-00", "io1": "V102-IO1-00", "vdp": "V102-VDP-00", "io2": "V102-IO2-00"}

PAGING = """<section class="dark sec"><div class="wrap"><h2>Turn the pages yourself</h2>
<p>One write to port 00h decides what the Z80 sees. Pick a ROM page, a RAM page and a mode. The map follows the board's decode logic.</p>
<form id="paging" class="builder"><div>
<fieldset class="seg"><legend>ROM page (R)</legend>%s</fieldset>
<fieldset class="seg"><legend>RAM page (P)</legend>%s</fieldset>
<fieldset class="seg"><legend>Mode</legend><label class="chip"><input type="checkbox" name="cpm"><span>CPM: all RAM</span></label></fieldset>
<p class="mono" id="outv" aria-live="polite"></p>
<p class="soft">Known fault: in all-RAM mode with R = 6, the 4000–7FFF block drops out. It is on the list for the next revision, and the map shows it.</p>
</div><ol class="mem" id="mem" aria-label="Memory map, top of memory first"></ol></form></div></section>""" % (
    "".join(f'<label class="chip"><input type="radio" name="r" value="{i}"{" checked" if i == 0 else ""}><span>{i}</span></label>' for i in range(8)),
    "".join(f'<label class="chip"><input type="radio" name="p" value="{i}"{" checked" if i == 0 else ""}><span>{i}</span></label>' for i in range(3)))

PORTS = [("CTC timer", 0x08), ("SIO serial", 0x0C), ("PIO parallel", 0x10), ("VDP data", 0x01), ("VDP control", 0x02), ("82C55 port A", 0x24), ("LCD command", 0x30)]
TRANSLATE = """<section class="dark sec"><div class="wrap"><h2>One port, two languages</h2>
<p>The Z80 has a separate space for I/O. The 6502 has only memory. The PLD opens a window at 7F00–7FEF and turns any access there into a Z80-style I/O cycle, so the other boards see the bus they were designed for.</p>
<div class="scroll"><table><thead><tr><th>Device</th><th>Z80 writes</th><th>6502 writes</th></tr></thead><tbody>%s</tbody></table></div>
<p class="soft">Zilog interrupts are the part that does not cross over yet: they need an acknowledge cycle and a RETI that the 6502 cannot give.</p></div></section>""" % "".join(
    f"<tr><td>{n}</td><td><code>OUT ({p:02X}h),A</code></td><td><code>STA $7F{p:02X}</code></td></tr>" for n, p in PORTS)
ORIGINAL = """<section class="paper sec"><div class="wrap"><h2>The machine it recreates</h2>
<p>The MTX 500 had 32 KB of RAM and the MTX512 had 64 KB. The second RAM chip on this board makes the same difference.</p>
<div class="pair"><figure class="photo "><img src="../assets/img/photo-mtx512-de.webp" width="1600" height="546" alt="Memotech MTX512 with a German keyboard layout"><figcaption>An MTX512, here with a German keyboard. <span class="cr">Photo: <a href="https://commons.wikimedia.org/wiki/File:Memotech_MTX512.jpg">Superandi73</a>, <a href="https://creativecommons.org/licenses/by-sa/3.0/">CC BY-SA 3.0</a>, resized.</span></figcaption></figure><figure class="photo cut"><img src="../assets/img/photo-mtx500-profiles.webp" width="1600" height="1100" alt="Memotech MTX500 from the back, top and side"><figcaption>The 32 KB MTX 500 from the back, top and side. <span class="cr">Photo: <a href="https://commons.wikimedia.org/wiki/File:Memotech_MTX500_profiles.jpg">Bilby</a>, <a href="https://creativecommons.org/licenses/by/3.0/">CC BY 3.0</a>, cropped and resized.</span></figcaption></figure></div></div></section>"""
EXTRA = {"mtx": ORIGINAL + PAGING, "6502": TRANSLATE}


def page(title, desc, body):
    return f"""<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)} · NOVAZ80</title>
<meta name="description" content="{E(desc)}">
<meta name="theme-color" content="#0b0b0d">
<link rel="icon" type="image/png" href="../assets/img/favicon.png">
<link rel="stylesheet" href="../assets/css/style.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<nav class="nav" aria-label="Main"><div class="wrap"><a class="brand" href="../index.html">NOVAZ80</a>
<ul><li><a href="../index.html#story">Story</a></li><li><a href="../design.html">Design</a></li><li><a href="../index.html#build">Build</a></li><li><a href="../index.html#bus">Bus</a></li><li><a href="../index.html#boards" aria-current="true">Boards</a></li></ul></div></nav>
<main id="main">
{body}
</main>
<footer><div class="wrap"><div class="bars"></div><p>NOVAZ80, by NOVA Embedded Solutions. A hobby project, built just for fun. <a href="../index.html">The story</a> · <a href="../credits.html">Credits</a></p></div></footer>
<script src="../assets/js/main.js" defer></script>
<script src="../assets/js/viewer.js" defer></script>
<script src="../assets/js/swipe.js" defer></script>
</body>
</html>
"""


def ul(items):
    return "<ul>" + "".join(f"<li>{E(x)}</li>" for x in items) + "</ul>"


def board(i, n, ids):
    d, (name, tag, facts) = DATA[i], META[i]
    ref = d["ref"]
    wide = i == "pr2"
    size = (1077, 397) if wide else (1042, 1064)
    seen = {p[0]: p for p in d["parts"]}
    spots = "".join(
        f'<button type="button" class="spot" data-p="{k}" style="left:{x}%;top:{y}%" aria-label="{E(str(k) + ", " + seen[str(k)][2])}">{k}</button>'
        for k, x, y in d["spots"])
    parts = "".join(
        f'<li><button type="button" data-p="{E(a)}"><span class="n">{E(a)}</span><span class="r">{E(r)}</span><span>{E(t)}</span></button></li>'
        for a, r, t in d["parts"])
    pld = ""
    if i in PLD:
        src = read(os.path.join(ROOT, "assets", "docs", PLD[i] + ".pld"))
        pld = f'<details><summary>Read the PLD source, {PLD[i]}</summary><pre class="code" tabindex="0">{E(src.strip())}</pre></details>'
    dls = [(f"V102-{ref[5:]}-schematic.pdf", "Schematic (PDF)"), (f"V102-{ref[5:]}-board.pdf", "Board layout (PDF)"), (f"V102-{ref[5:]}-bom.csv", "Parts list (CSV)")]
    if i in PLD:
        dls.append((PLD[i] + ".pld", "PLD source"))
    dl = "".join(f'<li><a href="../assets/docs/{f}">{t}</a></li>' for f, t in dls) + f'<li><a href="{i}-notes.html">Full design notes</a></li>'
    held = '<p class="small">Game and BIOS ROMs are not published.</p>' if i == "mtx" else ""
    pages = SHEETS.get(i, ["Main sheet"])
    mb = round(os.path.getsize(os.path.join(ROOT, "assets", "3d", i + ".glb")) / 1e6, 1)

    def sheet(k):
        return (f'href="../assets/docs/V102-{ref[5:]}-schematic.pdf" data-sheets="{len(pages)}" data-id="{i}" data-start="{k}" '
                f'data-title="{E(name)} schematic" data-labels="{"|".join(pages)}"')
    thumbs = "".join(f'<a class="sheet" {sheet(k)}><img src="../assets/sch/{i}-{k + 1}.webp" width="1100" height="778" alt="{E(name)} schematic, {t.lower()}"><span>{t}<b>Open</b></span></a>' for k, t in enumerate(pages))
    prev, nxt = ids[(n - 1) % len(ids)], ids[(n + 1) % len(ids)]
    body = f"""<header class="bhead"><div class="wrap"><div><p class="ref">{ref}<span class="pips" aria-hidden="true">{"".join('<i class="on"></i>' if k == i else "<i></i>" for k in ids)}</span></p><h1>{E(name)}</h1><p>{E(tag)}</p>
<dl class="facts">{"".join(f"<div><dt>{E(a)}</dt><dd>{E(b)}</dd></div>" for a, b in facts)}</dl><div class="btns"><a class="btn" {sheet(0)}>See the schematic</a></div></div>
<div class="model" data-glb="../assets/3d/{i}.glb"><img src="../assets/img/iso-{i}.webp" width="1300" height="850" alt="Render of the {E(name)}"><button type="button" class="mgo"><span>Rotate in 3D · {mb} MB</span></button></div></div></header>
<section class="dark sec"><div class="wrap"><h2>What's on the board</h2>
<div class="map{' wide' if wide else ''}"><div class="pic"><div class="inner"><img src="../assets/img/top-{i}.webp" width="{size[0]}" height="{size[1]}" alt="{E(name)} from above">{spots}</div></div><ol class="plist">{parts}</ol></div></div></section>
<section class="paper sec"><div class="wrap cols3"><div><h2>How it works</h2>{ul(d["how"])}</div><div><h2>What it took</h2>{ul(d["won"])}</div><div><h2>Next revision</h2>{ul(d["next"])}</div></div></section>
{EXTRA.get(i, "")}
<section class="dark sec" id="schematic"><div class="wrap"><h2>Schematic</h2><p class="soft">Tap to open it full screen, then pinch, scroll or drag to explore. It stays sharp at any zoom.</p>
<div class="sheets">{thumbs}</div></div></section>
<section class="paper sec"><div class="wrap"><h2>Photo and files</h2>
<div class="ph"><span class="tag">Live photo: board-{i}.jpg</span><b>The built {E(name)}</b><span>Straight down or three-quarter view, chips fitted, plain background.</span></div>
<h3 style="margin-top:36px">Downloads</h3><ul class="dl">{dl}</ul>{pld}{held}</div></section>
<section class="dark sec"><div class="wrap pn"><a rel="prev" href="{prev}.html">← {E(META[prev][0])}</a><a href="../index.html#boards">All boards</a><a rel="next" href="{nxt}.html">{E(META[nxt][0])} →</a></div></section>"""
    return page(name, tag, body)


def notes(i):
    md = MarkdownIt("commonmark").enable(["table", "strikethrough"])
    h = md.render(read(os.path.join(C, "notes", i + ".md")))
    h = h.replace("<table>", '<div class="scroll" tabindex="0"><table>').replace("</table>", "</table></div>").replace("<pre>", '<pre tabindex="0">')
    heads = []

    def head(m):
        k = f"s{len(heads)}"
        heads.append((k, m.group(1)))
        return f'<h2 id="{k}">{m.group(1)}</h2>'

    h = re.sub(r"<h2>(.*?)</h2>", head, h)
    toc = "".join(f'<li><a href="#{k}">{re.sub("<[^>]+>", "", x)}</a></li>' for k, x in heads)
    h = f'<details class="toc"><summary>Contents</summary><ul>{toc}</ul></details>' + h
    name = META[i][0]
    return page(name + " design notes", f"Design analysis of the NOVAZ80 {name}.",
                f'<section class="paper sec"><div class="wrap"><p><a class="more" href="{i}.html">← {E(name)}</a></p><article class="notes">{h}</article></div></section>')


def both():
    return ('<div class="pick"><input type="radio" name="asm" id="asm1" checked><label for="asm1">Stacked</label>'
            '<input type="radio" name="asm" id="asm2"><label for="asm2">Side by side</label>'
            f'<div class="pane p1">{diagrams.FIGS["stacked"]}</div><div class="pane p2">{diagrams.FIGS["flat"]}</div></div>')


PHASES = [("Mar 2022", "Single-board Z80 computer", ["Fully stand-alone, with timer and I/O", "No bigger than 100 × 100 mm, for economy"]),
          ("Apr 2022", "In-circuit programmer", ["Code, click and upload from VS Code", "Takes in software, firmware and hardware"]),
          ("May 2022", "Input/output module", ["Optional, for any CPU board", "Fits with or without the programmer"]),
          ("Aug 2022", "Video and sound module", ["Drives a display and an amplifier", "Fits with or without the programmer"]),
          ("Sep 2022", "6502 CPU module", ["A 6502 version with timer and I/O", "Stand-alone, or with the same programmer, I/O and video boards"]),
          ("Nov 2022", "Memotech MTX CPU module", ["Z80 and original binaries, to work identically to the MTX512", "Slots into the CPU position and reuses the video and I/O boards"])]
NOTES = [("In-circuit programmer", ["Program in assembly in a modern editor, VS Code.", "One click assembles, uploads to the programmer and on to the target."]),
         ("Three CPU board options", ["Stand-alone Z80 computer with on-board I/O and counter/timer.", "Swap-in 6502 version. Both work with the programmer, video and I/O boards.", "MTX512 CPU board: with the video and I/O boards it replicates the 1980s machine."]),
         ("Video and sound board", ["Optional for the Z80 and 6502.", "The same video and sound chips as the MTX512.", "Component or composite video, and sound, on RCA sockets."]),
         ("Input/output board", ["8-bit output latch and 8-bit input/output port.", "PS/2 keyboard, or an MTX512 matrix keyboard.", "Serial at up to 115,200 baud over DB9 or USB."])]


def design():
    li = lambda xs: "<ul>" + "".join(f"<li>{x}</li>" for x in xs) + "</ul>"
    phases = "".join(f'<li><time>{a}</time><b>Phase {k}: {t}</b>{li(x)}</li>' for k, (a, t, x) in enumerate(PHASES, 1))
    notes_ = "".join(f"<div><h3>{t}</h3>{li(x)}</div>" for t, x in NOTES)
    mach = "".join(f'<a class="mach" href="../boards/{i}.html"><img src="../assets/img/iso-{i}-sm.webp" width="640" height="418" alt=""><b>{t}</b>{li(x)}</a>' for i, t, x in (
        ("z80", "Z80 SBC", ["Z80 at 4 MHz, 32 K ROM, 32 K RAM, PIO and CTC on board", "Complete on its own", "Optional: I/O, video + sound, LCD"]),
        ("6502", "6502 SBC", ["W65C02S at 1 MHz with a VIA", "Its PLD maps a 6502 I/O window onto the Z80 port space", "Optional: the same I/O, video + sound and LCD boards"]),
        ("mtx", "Memotech MTX512", ["Z80 with the MTX ROM/RAM paging", "Runs the original BIOS, BASIC and games", "Required: the I/O and video + sound boards"])))
    return f"""<header class="dhead dark"><div class="wrap"><h1>How it fits together</h1>
<p class="lede">Rebuild the machines of the 1980s from real 8-bit parts. Recreate the Memotech MTX512 exactly. Learn by designing every layer, and make it modular rather than a one-off.</p>
<ul class="jump"><li><a href="#evolution">Evolution</a></li><li><a href="#bus">One bus</a></li><li><a href="#stacked">Stacked</a></li><li><a href="#flat">Side by side</a></li><li><a href="#machines">Machines</a></li><li><a href="#flow">Upload flow</a></li></ul></div></header>
<section class="paper sec" id="evolution"><div class="wrap"><h2>Conceptual evolution</h2><ol class="phases">{phases}</ol></div></section>
<section class="dark sec" id="bus"><div class="wrap"><h2>Identical boards, one bus</h2><div class="cols2"><div class="plainlist">{li(["Eight 8-way stacking sockets in the four corners carry address, data, control and power through every board.", "Any stacking order works electrically. Only tall parts limit placement.", "One CPU board plus any optional boards makes a complete machine."])}</div><div class="plainlist">{li(["Each CPU board's PLD turns its CPU's bus into the common Z80-style bus, so the I/O and video boards don't care which CPU drives them.", "The programmer takes the bus with BUSRQ and drives the ROM through ROMCSX, ROMWEX, ROMOEX and RESX, decoded by every CPU board."])}</div></div>
<p><a class="more" href="../index.html#bus">Explore all 64 bus pins</a></p></div></section>
<section class="paper sec" id="expansion"><div class="wrap"><h2>The v102 expansion philosophy</h2><p>Each v101 board carried its own selection of connectors. v102 is completely freeform: every bus line reaches every board, with a new auxiliary group for expansion. The programmer accepts both generations.</p>
{diagrams.FIGS["exp"]}
<div class="cols2"><div class="plainlist">{li(["Connectors are the long-pin, through-board type with the socket side down."])}</div><div class="plainlist">{li(["Unregulated power can enter at the programmer, but regulation happens on the CPU board, which feeds the rest."])}</div></div></div></section>
<section class="dark sec" id="stacked"><div class="wrap"><h2>Vertical stacking assembly</h2><p class="soft">Modules may be stacked in any sequence.</p>{diagrams.FIGS["stacked"]}<div class="cols4">{notes_}</div></div></section>
<section class="paper sec" id="flat"><div class="wrap"><h2>Development assembly</h2><p>The programmer becomes a backplane, with top access to all three main boards for debugging.</p>{diagrams.FIGS["flat"]}
<div class="cols2"><div class="plainlist">{li(["There are no electrical restrictions on position, although connectors such as the video board's RCA sockets dictate where some boards go.", "Raw 7.5–18 V DC goes to either the programmer or the CPU board."])}</div><div class="plainlist">{li(["Once a monitor has been programmed, the CPU board is stand-alone for the Z80 and 6502 systems.", "Extra MTX boards can be installed above the MTX CPU board."])}</div></div></div></section>
<section class="dark sec" id="machines"><div class="wrap"><h2>Three machines, one set of boards</h2><div class="machines">{mach}</div></div></section>
<section class="paper sec" id="flow"><div class="wrap"><h2>Code, click, upload</h2><p>Time runs downwards, and the upload travels left to right. Red and blue LEDs on the programmer blink at rates that match each stage.</p>{diagrams.flow()}
<p class="small">The first version ran from a script called MAKEIT.PY at 115,200 baud. Today it is uploadROM.py at 57,600.</p></div></section>"""


def write(name, text):
    with open(os.path.join(ROOT, "boards", name), "w", encoding="utf8", newline="\n") as f:
        f.write(text)


if __name__ == "__main__":
    ids = list(META)
    for n, i in enumerate(ids):
        write(i + ".html", board(i, n, ids))
        write(i + "-notes.html", notes(i))
    d = page("Design", "How the NOVAZ80 boards fit together: block diagrams, bus, machines and the upload flow.", design())
    with open(os.path.join(ROOT, "design.html"), "w", encoding="utf8", newline="\n") as f:
        f.write(d.replace("../", "").replace(' aria-current="true"', "").replace('<a href="design.html">Design', '<a href="design.html" aria-current="true">Design'))
    p = os.path.join(ROOT, "index.html")
    t = read(p)
    t = re.sub(r"(<!--diagrams-->).*?(<!--/diagrams-->)", lambda m: m[1] + both() + m[2], t, flags=re.S)
    with open(p, "w", encoding="utf8", newline="\n") as f:
        f.write(t)
    c = page("Credits", "Who and what NOVAZ80 owes its existence to.", read(os.path.join(C, "credits.html")))
    with open(os.path.join(ROOT, "credits.html"), "w", encoding="utf8", newline="\n") as f:
        f.write(c.replace("../", "").replace(' aria-current="true"', ""))
    print("built", len(ids) * 2 + 1, "pages")
