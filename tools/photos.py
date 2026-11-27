"""Make the site's web copies of the cut-out board photos.

Source: the transparent PNGs in PCBs/2-NOVAZ80-v102/photos (background already removed).
Output: assets/img/ph/<slug>-900.webp and -1600.webp (alpha kept, no metadata).
Needs Pillow. Only the photos listed here are published: the FPGA, UPS and
logic-analyser boards are held back until they are documented.
"""
import os
import sys
from PIL import Image

SRC = os.path.expanduser("~/OneDrive/Documents_OneDrive/PCBs/2-NOVAZ80-v102/photos")
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "img", "ph")

PHOTOS = {
    # the road to v102
    "leg-1": "be6502-side", "leg-2": "be6502-mon-side", "leg-3": "frst-z80-side",
    "leg-4": "scnd_z80_top", "leg-5": "z80-programable-side",
    "leg-6": "z80-icp2-side", "leg-7": "v001-ass-prog-side", "leg-9": "z80-stack-a",
    # story
    "mtx-stack": "mtx-stack-1", "stack-real": "z80-stack-b", "flat-real": "z80-flat-side-1",
    # board pages
    **{f"{b}-{v}": f"v102-{b}-{v}" for b in ("z80", "6502", "mtx", "io1", "vdp", "pr1", "pr2") for v in ("top", "side")},
    "io2-top": "v102-io2-top-lcd", "io2-side": "v102-io2-side-lcd", "io2-bare": "v102-io2-top",
    "pr2-flat": "z80-flat-top-2",
    "kbd-side": "v101-kbd-side", "kbd-top": "v101-kbd-top", "kbd-stack": "z80-stack-1", "kbd-first": "mtx-kbd1-top",
}


def main():
    os.makedirs(OUT, exist_ok=True)
    sizes = {}
    for slug, src in PHOTOS.items():
        im = Image.open(os.path.join(SRC, src + ".png")).convert("RGBA")
        for w in (900, 1600):
            c = im.copy()
            c.thumbnail((w, w), Image.LANCZOS)
            c.save(os.path.join(OUT, f"{slug}-{w}.webp"), "WEBP", quality=80, method=6)
            if w == 900:
                sizes[slug] = c.size
    for slug, (w, h) in sizes.items():
        print(f'"{slug}": ({w}, {h}),')


if __name__ == "__main__":
    sys.exit(main())
