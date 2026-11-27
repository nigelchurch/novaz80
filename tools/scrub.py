"""Remove the postal address and phone number from KiCad title blocks.

The NOVA Embedded Solutions drawing sheet prints the company name, then the
address and phone, in the cell beside the logo. This keeps the logo and the
company name and removes the rest, properly: the vector letters and the hidden
search text are deleted from the PDFs, and the pixels are repainted in the
schematic preview images. The cell is anchored to the bottom-right corner in
millimetres, so the same offsets work for A4, A3 and A2 sheets.

Needs PyMuPDF (pymupdf) and Pillow. Run after exporting new PDFs or previews:
    python tools/scrub.py            # fix files in place
    python tools/scrub.py --check    # report only; non-zero exit if anything is found
"""
import glob
import os
import sys

import pymupdf
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MM = 72 / 25.4
# address lines, as distances from the sheet's right and bottom edges (mm)
LEFT, RIGHT, TOP, BOTTOM = 124.5, 94.0, 29.6, 13.9
# the words to find live in tools/scrub-words.txt, one per line. It is kept out of git,
# because a list of the address would publish the address.
WORDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scrub-words.txt")
WORDS = [w.strip() for w in open(WORDS_FILE, encoding="utf8") if w.strip()]
SHEET_W_MM = 297.0  # schematic previews are whole A4 sheets


def area(w, h, unit):
    return (w - LEFT * unit, h - TOP * unit, w - RIGHT * unit, h - BOTTOM * unit)


def found(page):
    return [w for w in WORDS if page.search_for(w)]


def pdf(path, fix):
    doc = pymupdf.open(path)
    hits = []
    for n, page in enumerate(doc):
        if not found(page):
            continue
        hits.append(n)
        if not fix:
            continue
        # the hidden search text sits elsewhere on the sheet, so remove it word by word
        for w in WORDS:
            for r in page.search_for(w):
                page.add_redact_annot(r, fill=False)
        page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE, graphics=pymupdf.PDF_REDACT_LINE_ART_NONE,
                              text=pymupdf.PDF_REDACT_TEXT_REMOVE)
        # then the visible letters: every shape wholly inside the address lines goes
        r = pymupdf.Rect(*area(page.rect.width, page.rect.height, MM))
        page.add_redact_annot(r, fill=False)
        page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE, graphics=pymupdf.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED,
                              text=pymupdf.PDF_REDACT_TEXT_REMOVE)
    if fix and hits:
        doc.save(path + ".tmp", garbage=4, deflate=True)
        doc.close()
        os.replace(path + ".tmp", path)
    return hits


def preview(path, fix):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    box = [round(v) for v in area(w, h, w / SHEET_W_MM)]
    if fix:
        # repaint with the sheet colour, sampled just left of the address
        x, y = box[0] - 2, box[1] + 4
        col = im.getpixel((x, y))
        ImageDraw.Draw(im).rectangle(box, fill=col)
        im.save(path, "WEBP", quality=90, method=6)
    return box


def main():
    fix = "--check" not in sys.argv
    bad = 0
    for f in sorted(glob.glob(os.path.join(ROOT, "assets", "docs", "*.pdf"))):
        hits = pdf(f, fix)
        left = pdf(f, False) if fix else hits
        print(f"{os.path.basename(f):34} {'cleaned' if fix and hits else 'clean' if not hits else 'ADDRESS FOUND'} {'' if not left else 'STILL FOUND on pages ' + str(left)}")
        bad += bool(left)
    if fix:
        for f in sorted(glob.glob(os.path.join(ROOT, "assets", "sch", "*.webp"))):
            if os.path.basename(f).startswith("6502-"):
                continue  # the 6502 sheets use a plain title block
            preview(f, True)
            print(f"{os.path.basename(f):34} repainted")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
