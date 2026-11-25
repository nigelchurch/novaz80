"""Block diagrams redrawn from the project deck, each in a wide and a tall (phone) layout."""


class D:
    def __init__(self, w, h, cls, label):
        self.w, self.h, self.cls, self.label, self.o = w, h, cls, label, []

    def add(self, s):
        self.o.append(s)

    def board(self, x, y, w, h, name, at="end"):
        self.add(f'<rect class="db" x="{x}" y="{y}" width="{w}" height="{h}" rx="10"/>')
        tx = x + w - 12 if at == "end" else x + 12
        self.add(f'<text class="dn" x="{tx}" y="{y + h - 11}" text-anchor="{at}">{name}</text>')

    def chip(self, x, y, w, h, *lines, cls="dc"):
        self.add(f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="3"/>')
        n = len(lines)
        for i, t in enumerate(lines):
            self.add(f'<text class="dt" x="{x + w / 2}" y="{y + h / 2 + 5 + (i - (n - 1) / 2) * 19}" text-anchor="middle">{t}</text>')

    def text(self, x, y, t, cls="dl", anchor="middle", rot=0):
        r = f' transform="rotate({rot} {x} {y})"' if rot else ""
        self.add(f'<text class="{cls}" x="{x}" y="{y}" text-anchor="{anchor}"{r}>{t}</text>')

    def line(self, pts, cls="da", both=False, dash=False):
        m = f' marker-end="url(#{self.cls}-{cls})"' if not dash else ""
        if both:
            m += f' marker-start="url(#{self.cls}-{cls})"'
        self.add(f'<polyline class="{cls}{" dd" if dash else ""}" points="{" ".join(f"{a},{b}" for a, b in pts)}"{m}/>')

    def fat(self, x1, y1, x2, y2, t=15, cls="dbus", label=None):
        """double-headed block arrow, horizontal or vertical"""
        h = t * 1.75
        if y1 == y2:
            hd = min(18, abs(x2 - x1) / 2.4)
            p = [(x1, y1), (x1 + hd, y1 - h), (x1 + hd, y1 - t), (x2 - hd, y1 - t), (x2 - hd, y1 - h), (x2, y1), (x2 - hd, y1 + h), (x2 - hd, y1 + t), (x1 + hd, y1 + t), (x1 + hd, y1 + h)]
        else:
            hd = min(18, abs(y2 - y1) / 2.4)
            p = [(x1, y1), (x1 - h, y1 + hd), (x1 - t, y1 + hd), (x1 - t, y2 - hd), (x1 - h, y2 - hd), (x1, y2), (x1 + h, y2 - hd), (x1 + t, y2 - hd), (x1 + t, y1 + hd), (x1 + h, y1 + hd)]
        self.add(f'<polygon class="{cls}" points="{" ".join(f"{a:.1f},{b:.1f}" for a, b in p)}"/>')
        if label:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            if y1 == y2:
                self.add(f'<text class="dbt" x="{mx}" y="{my + 5}" text-anchor="middle">{label}</text>')
            else:
                self.add(f'<text class="dbt" x="{mx}" y="{my}" text-anchor="middle" dominant-baseline="central" transform="rotate(-90 {mx} {my})">{label}</text>')

    def pc(self, x, y):
        self.add(f'<g class="dpc" transform="translate({x} {y})"><rect x="0" y="0" width="62" height="42" rx="4"/><rect class="scr" x="5" y="5" width="52" height="32"/><path d="M24 42h14l4 9H20z"/><rect x="70" y="0" width="22" height="51" rx="3"/></g>')

    def svg(self):
        ms = "".join(f'<marker id="{self.cls}-{c}" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="m{c}" d="M0 0L10 5L0 10z"/></marker>' for c in ("da", "dp"))
        return f'<svg class="{self.cls.split("-")[0]}" viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{self.label}"><defs>{ms}</defs>{"".join(self.o)}</svg>'


STACK = "Block diagram of the stacked machine: programmer, CPU, video and I/O boards joined by one bus. The CPU board makes 5 volts for the others."


def stacked_wide():
    d = D(1240, 560, "wide-st", STACK)
    X, Y, WD, HT = [20, 335, 650, 965], 190, 235, 250
    for x, n in zip(X, ("Programmer board", "CPU board", "Video board", "I/O board")):
        d.board(x, Y, WD, HT, n, "start" if n.startswith("Prog") else "end")
    for i in range(3):
        d.fat(X[i] + WD - 8, Y + 36, X[i + 1] + 8, Y + 36, 13, label="BUS")
    a, c, v, p = X[1], X[2], X[3], X[0]
    d.chip(p + 24, Y + 66, WD - 62, 118, "In-circuit", "parallel", "programmer")
    for cx, cy, t in ((20, 66, "CPU"), (123, 66, "PIO"), (20, 116, "ROM"), (123, 116, "RAM"), (20, 166, "5 V DC")):
        d.chip(a + cx, Y + cy, 94, 40, t)
    d.fat(p + WD - 38, Y + 136, a + 20, Y + 136, 11, "dr")
    d.line([(a + 20, Y + 178), (p + WD - 36, Y + 178)], "dp")
    d.text(X[0] + WD + 40, Y + 171, "5 V", "ds")
    for cx, cy, t in ((20, 66, "VDP"), (123, 66, "Sound"), (20, 116, "VRAM")):
        d.chip(c + cx, Y + cy, 94, 40, t)
    d.chip(v + 20, Y + 66, 82, 40, "UART")
    d.chip(v + 134, Y + 66, 82, 40, "FTDI")
    d.fat(v + 102, Y + 86, v + 134, Y + 86, 6, "dr")
    d.chip(v + 20, Y + 116, 196, 40, "Parallel I/O")
    d.chip(v + 20, Y + 166, 196, 40, "Counter / timer")
    for i in (1, 2):
        d.line([(X[i] + WD, Y + 90), (X[i + 1], Y + 90)], "dp")
        d.text(X[i] + WD + 40, Y + 84, "5 V", "ds")
    d.pc(p + 92, 28)
    d.line([(p + 137, 88), (p + 137, Y + 66)], both=True)
    d.text(p + 146, 140, "USB", "ds", "start")
    for x, n, via, both in ((c + 67, "YPbPr video", "RCA", 0), (c + 170, "Audio", "RCA", 0), (v + 61, "Serial COM1", "DB9", 1), (v + 175, "Serial USB", "USB", 1)):
        d.line([(x, Y + 66), (x, 88)], both=bool(both))
        d.text(x, 74, n)
        d.text(x + 9, 140, via, "ds", "start")
    d.line([(a + 67, 506), (a + 67, Y + 207)], "dp")
    d.line([(p + 212, 506), (p + 212, Y + 197), (a + 19, Y + 197)], "dp")
    d.text(p + 212, 528, "Raw DC, 7.5–18 V")
    d.text(a + 67, 528, "Raw DC, 7.5–18 V")
    d.text((p + 212 + a + 67) / 2 + 1, 488, "or", "ds")
    return d.svg()


def stacked_tall():
    d = D(380, 1000, "tall-st", STACK)
    x, w = 10, 360
    # I/O
    y = 70
    d.board(x, y, w, 172, "I/O board")
    d.chip(150, y + 14, 92, 36, "UART")
    d.chip(268, y + 14, 92, 36, "FTDI")
    d.fat(242, y + 32, 268, y + 32, 6, "dr")
    d.chip(150, y + 58, 210, 34, "Parallel I/O")
    d.chip(150, y + 100, 210, 34, "Counter / timer")
    for cx, n, via in ((196, "Serial COM1", "DB9"), (314, "Serial USB", "USB")):
        d.line([(cx, y + 14), (cx, 34)], both=True)
        d.text(cx, 24, n)
        d.text(cx + 8, 58, via, "ds", "start")
    # video
    y2 = 320
    d.board(x, y2, w, 120, "Video board")
    d.chip(150, y2 + 14, 92, 36, "VDP")
    d.chip(268, y2 + 14, 92, 36, "Sound")
    d.chip(150, y2 + 58, 92, 34, "VRAM")
    for cx, n in ((196, "YPbPr video"), (314, "Audio")):
        d.line([(cx, y2 + 14), (cx, 272)])
        d.text(cx, 263, n)
        d.text(cx + 8, 300, "RCA", "ds", "start")
    # cpu
    y3 = 534
    d.board(x, y3, w, 132, "")
    d.text(202, y3 + 113, "CPU board", "dn", "start")
    d.chip(24, y3 + 14, 92, 36, "CPU")
    d.chip(134, y3 + 14, 92, 36, "PIO")
    d.chip(264, y3 + 14, 96, 78, "5 V DC")
    d.chip(24, y3 + 58, 92, 34, "ROM")
    d.chip(134, y3 + 58, 92, 34, "RAM")
    d.line([(312, 500), (312, y3 + 14)], "dp")
    d.text(312, 478, "Raw DC")
    d.text(312, 494, "7.5–18 V", "ds")
    # programmer
    y4 = 750
    d.board(x, y4, w, 124, "")
    d.text(326, y4 + 113, "Programmer board", "dn", "end")
    d.chip(24, y4 + 16, 202, 76, "In-circuit", "parallel programmer")
    d.fat(70, y3 + 92, 70, y4 + 16, 10, "dr")
    d.line([(286, y3 + 92), (286, y4 + 40), (227, y4 + 40)], "dp")
    d.text(278, y4 - 18, "5 V", "ds", "end")
    d.line([(336, 960), (336, y3 + 93)], "dp")
    d.text(328, 945, "or raw DC, 7.5–18 V", "dl", "end")
    d.pc(70, 918)
    d.line([(116, 912), (116, y4 + 92)], both=True)
    d.text(126, 898, "USB", "ds", "start")
    # bus and 5 V between boards
    d.fat(56, y + 164, 56, y2 + 8, 14, label="BUS")
    d.fat(56, y2 + 112, 56, y3 + 8, 14, label="BUS")
    d.fat(180, y3 + 124, 180, y4 + 8, 14, label="BUS")
    d.line([(112, y2), (112, y + 172)], "dp")
    d.text(120, 280, "5 V", "ds", "start")
    d.line([(112, y3), (112, y2 + 120)], "dp")
    d.text(120, 492, "5 V", "ds", "start")
    return d.svg()


FLAT = "Block diagram of the development assembly: CPU, I/O and video boards side by side on the programmer, which acts as a backplane."


def flat_wide():
    d = D(1240, 680, "wide-fl", FLAT)
    X, Y, WD, HT, B = [200, 545, 890], 120, 320, 232, 450
    for x, n in zip(X, ("CPU board", "I/O board", "Video board")):
        d.board(x, Y, WD, HT, n, "end" if n.startswith("CPU") else "start")
    d.add(f'<rect class="db" x="200" y="{B}" width="1010" height="200" rx="10"/>')
    d.text(216, B + 186, "Programmer board", "dn", "start")
    for cx, cy, t in ((20, 24, "CPU"), (134, 24, "PIO"), (20, 78, "RAM"), (134, 78, "ROM"), (20, 132, "5 V DC")):
        d.chip(X[0] + cx, Y + cy, 102, 42, t)
    v = X[1]
    d.chip(v + 20, Y + 24, 102, 42, "UART")
    d.chip(v + 158, Y + 24, 102, 42, "FTDI")
    d.fat(v + 122, Y + 45, v + 158, Y + 45, 7, "dr")
    d.chip(v + 20, Y + 78, 240, 42, "Parallel I/O")
    d.chip(v + 20, Y + 132, 240, 42, "Counter / timer")
    c = X[2]
    for cx, cy, t in ((20, 24, "VDP"), (158, 24, "Sound"), (20, 78, "VRAM")):
        d.chip(c + cx, Y + cy, 102, 42, t)
    for x in X:
        d.fat(x + 286, Y + HT - 4, x + 286, B + 4, 13, label="BUS")
    d.chip(228, B + 78, 250, 78, "In-circuit", "parallel programmer")
    d.fat(X[0] + 185, Y + 120, X[0] + 185, B + 78, 12, "dr")
    # power
    d.line([(60, Y + 153), (X[0] + 20, Y + 153)], "dp")
    d.text(66, Y + 120, "Raw DC", "dl", "start")
    d.text(66, Y + 138, "7.5–18 V", "ds", "start")
    d.line([(60, B + 34), (X[0] + 52, B + 34), (X[0] + 52, Y + 175)], "dp")
    d.text(66, B + 2, "Raw DC", "dl", "start")
    d.text(66, B + 20, "7.5–18 V", "ds", "start")
    d.text(66, 372, "or", "ds", "start")
    d.line([(X[0] + 100, Y + 174), (X[0] + 100, B + 78)], "dp")
    d.text(X[0] + 108, 408, "5 V", "ds", "start")
    d.line([(X[0] + 100, B + 52), (v + 200, B + 52), (v + 200, Y + HT)], "dp")
    d.line([(v + 200, B + 52), (c + 200, B + 52), (c + 200, Y + HT)], "dp")
    for x in (v + 208, c + 208):
        d.text(x, 408, "5 V", "ds", "start")
    d.pc(30, B + 94)
    d.line([(128, B + 118), (228, B + 118)], both=True)
    d.text(166, B + 110, "USB", "ds")
    for x, n, via, both in ((v + 71, "Serial COM1", "DB9", 1), (v + 209, "Serial USB", "USB", 1), (c + 71, "YPbPr video", "RCA", 0), (c + 209, "Audio", "RCA", 0)):
        d.line([(x, Y + 24), (x, 44)], both=bool(both))
        d.text(x, 32, n)
        d.text(x + 9, 92, via, "ds", "start")
    return d.svg()


def flat_tall():
    d = D(380, 960, "tall-fl", FLAT)
    d.add('<rect class="db" x="10" y="60" width="112" height="770" rx="10"/>')
    d.text(40, 600, "Programmer board", "dn", "start", -90)
    R, WD = 186, 184
    ys = {"v": 80, "i": 350, "c": 620}
    y = ys["v"]
    d.board(R, y, WD, 150, "Video board")
    d.chip(R + 12, y + 14, 76, 36, "VDP")
    d.chip(R + 96, y + 14, 76, 36, "Sound")
    d.chip(R + 12, y + 58, 76, 36, "VRAM")
    for cx, n in ((R + 50, "Video"), (R + 134, "Audio")):
        d.line([(cx, y + 14), (cx, 36)])
        d.text(cx, 26, n)
        d.text(cx + 7, 66, "RCA", "ds", "start")
    y = ys["i"]
    d.board(R, y, WD, 176, "I/O board")
    d.chip(R + 12, y + 14, 70, 36, "UART")
    d.chip(R + 102, y + 14, 70, 36, "FTDI")
    d.fat(R + 82, y + 32, R + 102, y + 32, 5, "dr")
    d.chip(R + 12, y + 58, 160, 36, "Parallel I/O")
    d.chip(R + 12, y + 102, 160, 36, "Counter / timer")
    for cx, n, via in ((R + 47, "COM1", "DB9"), (R + 137, "USB", "USB")):
        d.line([(cx, y + 14), (cx, 296)], both=True)
        d.text(cx, 285, n)
        d.text(cx + 7, 334, via, "ds", "start")
    y = ys["c"]
    d.board(R, y, WD, 190, "CPU board")
    d.chip(R + 12, y + 14, 76, 36, "5 V DC")
    d.chip(R + 96, y + 14, 76, 36, "CPU")
    d.chip(R + 12, y + 100, 76, 36, "ROM")
    d.chip(R + 96, y + 58, 76, 36, "RAM")
    d.chip(R + 96, y + 100, 76, 36, "PIO")
    d.line([(R + 50, 584), (R + 50, y + 14)], "dp")
    d.text(R + 6, 560, "Raw DC", "dl", "start")
    d.text(R + 6, 577, "7.5–18 V", "ds", "start")
    for yy in (ys["v"] + 118, ys["i"] + 140, y + 166):
        d.fat(116, yy, R + 6, yy, 11, label="BUS")
    d.add(f'<rect class="dc" x="16" y="{y + 22}" width="82" height="124" rx="3"/>')
    for k, t in enumerate(("In-circuit", "parallel", "program-", "mer")):
        d.text(57, y + 60 + k * 20, t, "dt")
    d.fat(98, y + 118, R + 12, y + 118, 9, "dr")
    d.line([(R + 12, y + 34), (99, y + 34)], "dp")
    d.text(148, y + 28, "5 V", "ds")
    d.line([(80, y + 22), (80, ys["i"] + 80), (R, ys["i"] + 80)], "dp")
    d.line([(80, ys["i"] + 80), (80, ys["v"] + 70), (R, ys["v"] + 70)], "dp")
    for yy in (ys["i"] + 73, ys["v"] + 63):
        d.text(152, yy, "5 V", "ds")
    d.pc(8, 890)
    d.line([(50, 884), (50, y + 146)], both=True)
    d.text(58, 866, "USB", "ds", "start")
    d.line([(110, 936), (110, y + 72), (R + 30, y + 72), (R + 30, y + 51)], "dp")
    d.text(124, 910, "or raw DC, 7.5–18 V", "dl", "start")
    d.text(124, 928, "through the programmer", "ds", "start")
    return d.svg()


# ---- v101 to v102 connector plan
def strip(d, x, y, w, h, c, label=None):
    d.add(f'<rect class="k-{c}" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="1.5"><title>{c.upper()}</title></rect>')
    if label:
        vert = h > w
        cx, cy = x + w / 2, y + h / 2
        d.add(f'<text class="kt kt-{c}" x="{cx:.1f}" y="{cy:.1f}" text-anchor="middle" dominant-baseline="central"' + (f' transform="rotate(-90 {cx:.1f} {cy:.1f})"' if vert else "") + f'>{label}</text>')


def v101(d, x, y, s, kind):
    d.add(f'<rect class="db" x="{x}" y="{y}" width="{s}" height="{s}" rx="{s * .07:.1f}"/>')
    L, T, m = s * .25, s * .052, s * .035
    e = s * .075
    if kind == "Video":
        strip(d, x + m, y + e, T, L, "addr"); strip(d, x + s - m - T, y + e, T, L, "spec")
        strip(d, x + m, y + s - e - L, T, L, "data"); strip(d, x + s - m - T, y + s - e - L, T, L, "ctrl")
    else:
        strip(d, x + e, y + m, L, T, "addr"); strip(d, x + s - e - L, y + m, L, T, "spec")
        strip(d, x + e, y + s - m - T, L, T, "data"); strip(d, x + s - e - L, y + s - m - T, L, T, "ctrl")
        if kind == "CPU":
            strip(d, x + s * .345, y + m, s * .15, T, "a8"); strip(d, x + s * .505, y + m, s * .15, T, "prog")
    d.text(x + s / 2, y + s / 2 - 4, "v101", "dn"); d.text(x + s / 2, y + s / 2 + 16, kind, "dn")


def v102(d, x, y, s, big=False, pad=False):
    d.add(f'<rect class="{"dpad" if pad else "db"}" x="{x}" y="{y}" width="{s}" height="{s}" rx="{s * .07:.1f}"/>')
    L, T, m, e = s * .25, s * (.058 if big else .052), s * .03, s * .075
    g = T + s * .012
    n = (lambda t: t) if big else (lambda t: None)
    strip(d, x + e, y + m, L, T, "addr", n("A0–A7")); strip(d, x + e, y + m + g, L, T, "a8", n("A8–A15"))
    strip(d, x + s - e - L, y + m, L, T, "spec", n("SPEC")); strip(d, x + s - e - L, y + m + g, L, T, "prog", n("PROG"))
    strip(d, x + m, y + s - m - T - s * .02 - L, T, L, "data", n("DATA")); strip(d, x + m + g, y + s - m - T - s * .02 - L, T, L, "spare", n("SPARE"))
    strip(d, x + s - m - T, y + s - m - T - s * .02 - L, T, L, "ctrl", n("CTRL")); strip(d, x + s - m - T - g, y + s - m - T - s * .02 - L, T, L, "mtx", n("MTX"))
    if pad or big:
        u = y + m + 2.35 * g
        strip(d, x + m, u, T, L * .9, "addr"); strip(d, x + s - m - T, u, T, L * .9, "spec")
        strip(d, x + e + g, y + s - m - T, L, T, "data"); strip(d, x + s - e - L - g, y + s - m - T, L, T, "ctrl")
    if pad:
        strip(d, x + s * .345, y + m, s * .15, T, "a8"); strip(d, x + s * .505, y + m, s * .15, T, "prog")
    if big:
        d.text(x + s / 2, y + s / 2 - 8, "v102", "dn big"); d.text(x + s / 2, y + s / 2 + 20, "any board", "dn")


EXP = "How v102 grew from v101: three different connector layouts become one, and the three-pad programmer accepts both."
KEYS = [("addr", "A0–A7"), ("a8", "A8–A15"), ("data", "DATA"), ("ctrl", "CTRL"), ("spec", "SPEC, 5 V / 0 V"), ("prog", "PROG"), ("mtx", "MTX"), ("spare", "SPARE (AUX)")]


def exp_wide():
    d = D(1240, 640, "wide-ex", EXP)
    v102(d, 20, 300, 300, big=True)
    for i, k in enumerate(("Video", "I/O", "CPU")):
        v101(d, 400 + i * 278, 20, 244, k)
    d.add('<rect class="dbk" x="384" y="300" width="836" height="300" rx="22"/>')
    for i in range(3):
        v102(d, 400 + i * 278, 316, 244, pad=True)
        d.line([(522 + i * 278, 266), (522 + i * 278, 298)])
    d.text(802, 586, "Three-pad programmer: every pad takes v101 or v102", "dn")
    d.line([(322, 450), (382, 450)])
    for i, (c, t) in enumerate(KEYS):
        x, y = 24 + (i % 2) * 178, 36 + (i // 2) * 44
        strip(d, x, y, 40, 16, c)
        d.text(x + 50, y + 13, t, "dl", "start")
    return d.svg()


def exp_tall():
    d = D(380, 1010, "tall-ex", EXP)
    for i, k in enumerate(("Video", "I/O", "CPU")):
        v101(d, 8 + i * 124, 10, 116, k)
        d.line([(66 + i * 124, 128), (66 + i * 124, 170)])
    d.add('<rect class="dbk" x="1" y="172" width="378" height="156" rx="14"/>')
    for i in range(3):
        v102(d, 8 + i * 124, 180, 116, pad=True)
    d.text(190, 317, "Three-pad programmer takes both", "dn")
    d.line([(190, 392), (190, 332)])
    v102(d, 40, 396, 300, big=True)
    for i, (c, t) in enumerate(KEYS):
        x, y = 20 + (i % 2) * 180, 740 + (i // 2) * 44
        strip(d, x, y, 40, 16, c)
        d.text(x + 50, y + 13, t, "dl", "start")
    d.h = 920
    return d.svg()


def figure(key, title, wide, tall):
    return (f'<figure class="diagram" id="{key}" data-title="{title}">{wide}{tall}'
            f'<button type="button" class="zoom" data-diagram="{key}" aria-label="Open {title} full screen">⤢ Full screen</button></figure>')


FIGS = {
    "stacked": figure("d-stacked", "Stacked assembly", stacked_wide(), stacked_tall()),
    "flat": figure("d-flat", "Development assembly", flat_wide(), flat_tall()),
    "exp": figure("d-exp", "From v101 to v102", exp_wide(), exp_tall()),
}

# upload flow: lane texts (pc, programmer, target) and arrows between lanes: > < or none
FLOW = [
    ("Write assembly in VS Code and click make", "", "Wait", "", "Run the program in ROM"),
    ("Assemble and link into one binary (vasm)", "", "", "", ""),
    ("Python script finds the programmer's port and connects", "", "", "", ""),
    ("Send the binary", ">", "Wake up and store it in serial RAM", "", ""),
    ("Wait for reply", "", "Keep storing until the end-of-file marker", "", ""),
    ("Check the echo against the file", "<", "Send it back for checking", "", ""),
    ("Send the go-ahead", ">", "Take control of the target's bus", ">", "CPU lets go of the bus"),
    ("Show progress", "<", "Upload the binary to the ROM", ">", "ROM is written"),
    ("Show progress", "<", "Read the ROM back and compare", "<", "ROM is read"),
    ("End the session", "", "Release the bus and reset the target", ">", "Run the new program"),
]


def flow():
    rows = ""
    for i, (a, x, b, y, c) in enumerate(FLOW):
        def cell(t, lane):
            return f'<span class="fl {lane}">{t}</span>' if t else f'<span class="fl no"></span>'

        def arr(s):
            return f'<i class="fa {"r" if s == ">" else "l" if s == "<" else "n"}" aria-hidden="true">{"→" if s == ">" else "←" if s == "<" else ""}</i>'
        rows += f'<li>{cell(a, "pc")}{arr(x)}{cell(b, "pr")}{arr(y)}{cell(c, "ta")}</li>'
    return ('<div class="flow"><div class="fhead" aria-hidden="true"><b>Your PC</b><i></i><b>Programmer</b><i></i><b>CPU board</b></div>'
            f'<ol>{rows}</ol></div>')
