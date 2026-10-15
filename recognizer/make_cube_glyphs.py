"""Draw the numbers of the doubling cube in ordinary fonts for cube_value.py (TODO-025).

Writes cube_glyphs.png: one row per font in TEMPLATE_FONTS, one GLYPH x GLYPH square per value
(2, 4, 8, 16, 32, 64), white ink on black. Run again only to change the fonts:

  uv run python recognizer/make_cube_glyphs.py      # needs Pillow (a dev dependency) and the fonts

TEST_FONTS are kept apart: synth_cube.py draws the cubes it pastes into photos with them, so the
reader is checked on fonts it has never seen. Fonts are found with fc-match (fontconfig).
"""
from __future__ import annotations

import os
import subprocess
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cube_value  # noqa: E402

TEMPLATE_FONTS = [
    "DejaVu Sans:Bold", "DejaVu Sans", "DejaVu Serif:Bold", "Liberation Sans:Bold", "Liberation Sans",
    "Liberation Serif:Bold", "FreeSans:Bold", "Carlito:Bold", "Inter:Bold", "Inter", "Poppins:Bold",
    "Poppins", "TeX Gyre Heros:Bold", "TeX Gyre Heros Cn:Bold", "TeX Gyre Termes:Bold",
    "TeX Gyre Chorus", "Lora:Bold", "Utopia:Bold", "Noto Sans CJK JP:Bold",
]
TEST_FONTS = [
    "Bitstream Charter:Bold", "Caladea:Bold", "Courier 10 Pitch:Bold", "FreeSerif:Bold",
    "GFS Baskerville", "Inter Display:Bold", "Latin Modern Sans:Bold", "TeX Gyre Adventor:Bold",
    "TeX Gyre Pagella:Bold", "TeX Gyre Schola:Bold", "Noto Serif CJK JP:Bold", "Liberation Mono:Bold",
]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cube_glyphs.png")


def font_file(pattern):
    return subprocess.run(["fc-match", "-f", "%{file}", pattern], capture_output=True, text=True, check=True).stdout


def draw(text, pattern, size=200):
    """The text in the font, white on black (8 bits), cropped to its ink."""
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.truetype(font_file(pattern), size)
    img = Image.new("L", (size * 3, size * 2), 0)
    ImageDraw.Draw(img).text((size // 4, size // 4), text, fill=255, font=font)
    a = np.asarray(img)
    ys, xs = np.nonzero(a > 127)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def main():
    rows = []
    for pattern in TEMPLATE_FONTS:
        row = [cube_value._fit(draw(str(v), pattern) > 127) for v in cube_value.VALUES]
        rows.append(np.hstack(row))
        print(f"{pattern:28s} {font_file(pattern)}")
    cv2.imwrite(OUT, (np.vstack(rows) * 255).astype(np.uint8))
    print("wrote", OUT, len(rows), "fonts")


if __name__ == "__main__":
    main()
