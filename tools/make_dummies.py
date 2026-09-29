"""Make the placeholder pictures, werkblad PDFs and app icons for the two dummy questions.

Run from anywhere:  python tools/make_dummies.py
Needs Pillow and PyMuPDF (fitz). The dummies hold no maths at all.
"""
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
ICONS = ROOT / "icons"


def font(size, bold=True):
    names = ["arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf"] if bold else ["arial.ttf", "DejaVuSans.ttf"]
    for name in names:
        for base in ("C:/Windows/Fonts", "/usr/share/fonts/truetype/dejavu", ""):
            try:
                return ImageFont.truetype(str(Path(base) / name) if base else name, size)
            except OSError:
                continue
    return ImageFont.load_default()


def picture(path, lines, height=520):
    """White 1600 px wide picture with dark text, one thin grey frame."""
    img = Image.new("RGB", (1600, height), "white")
    d = ImageDraw.Draw(img)
    d.rectangle([24, 24, 1575, height - 25], outline=(190, 190, 190), width=3)
    big, small = font(96), font(48, bold=False)
    y = 120
    for i, text in enumerate(lines):
        f = big if i == 0 else small
        w = d.textlength(text, font=f)
        d.text(((1600 - w) / 2, y), text, fill=(20, 24, 36), font=f)
        y += 150 if i == 0 else 80
    img.save(path, optimize=True)


def werkblad(path, n):
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4 portrait, points
    page.insert_text((72, 140), "DUMMY WERKBLAD", fontsize=36, fontname="helv")
    page.insert_text((72, 200), f"Vraag {n}", fontsize=28, fontname="helv")
    page.insert_text((72, 250), "Hierdie bladsy is 'n plekhouer sonder inhoud.", fontsize=14, fontname="helv")
    doc.save(path)
    doc.close()


def icon(path, size):
    img = Image.new("RGB", (size, size), (7, 11, 22))
    d = ImageDraw.Draw(img)
    pad = max(2, size // 32)
    d.rectangle([pad, pad, size - pad - 1, size - pad - 1], outline=(58, 160, 255), width=max(2, size // 64))
    f = font(int(size * 0.46))
    text = "V4"
    box = d.textbbox((0, 0), text, font=f)
    w, h = box[2] - box[0], box[3] - box[1]
    d.text(((size - w) / 2 - box[0], (size - h) / 2 - box[1]), text, fill=(58, 160, 255), font=f)
    img.save(path, optimize=True)


def main():
    v01 = CONTENT / "v01"
    v02 = CONTENT / "v02"
    v01.mkdir(parents=True, exist_ok=True)
    v02.mkdir(parents=True, exist_ok=True)

    picture(v01 / "vraag-1.png", ["DUMMY VRAAG 1", "Toetsvraag sonder inhoud"], height=900)
    for i in (1, 2, 3):
        picture(v01 / f"wenk-{i}.png", [f"DUMMY WENK {i}", "(VRAAG 1)"])
    picture(v01 / "roete-1.png", ["DUMMY ROETE 1", "(VRAAG 1)"], height=700)
    picture(v01 / "oplossing-1.png", ["DUMMY OPLOSSING 1", "(VRAAG 1)"], height=700)
    werkblad(v01 / "werkblad-v01.pdf", 1)

    picture(v02 / "vraag-1.png", ["DUMMY VRAAG 2", "Toetsvraag sonder inhoud"], height=900)
    picture(v02 / "roete-1.png", ["DUMMY ROETE 2", "(VRAAG 2)"], height=700)
    picture(v02 / "oplossing-1.png", ["DUMMY OPLOSSING 2", "(VRAAG 2)"], height=700)
    werkblad(v02 / "werkblad-v02.pdf", 2)

    ICONS.mkdir(exist_ok=True)
    icon(ICONS / "icon-192.png", 192)
    icon(ICONS / "icon-512.png", 512)
    print("dummies and icons written")


if __name__ == "__main__":
    main()
