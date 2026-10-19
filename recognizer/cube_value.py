"""Read the number on the doubling cube's face (TODO-025): 2, 4, 8, 16, 32 or 64.

The face is cut out of the board seen from straight above (cube.py finds it), turned square and
upright, and its ink compared with the numbers drawn in many fonts, in each of the four ways the
cube can face: the strokes of both are thinned to one pixel and scored by how far apart they lie,
so a bold and a thin font of the same number still match. Nothing here is learnt from photos: the
shapes are OpenCV's own (Hershey) fonts and ordinary fonts drawn once into cube_glyphs.png
(make_cube_glyphs.py), so a real cube's font is never one of them, and the scores leave room for that.

Integers only (CLAUDE.md, TODO-046): the face is cut out with exact.warp, the ink found with
Otsu's threshold on 8 bits, shrunk by counting pixels, and the shapes compared by counting too.
"""

from __future__ import annotations

import math
import os

import cv2
import numpy as np

import exact

VALUES = (2, 4, 8, 16, 32, 64)
FACE = 80  # the face is cut out at this many pixels a side
INNER = 0.90  # of the face's side, kept (beyond it: the edge of the cube, the board)
RING = 0.10  # the band along the edge of what is kept, of its side: marks mostly in it are the bevel or a shadow
GLYPH = 48  # the ink is fitted into a square this many pixels a side
INK_MIN = 0.03  # ink, at least, of the inner face
INK_MAX = 0.45  # and at most (more is not a number: a shadow, another face)
SCORE_MIN = 0.74  # the best match, at least (0..1: 1 - the strokes' mean distance apart / DIST_SCALE)
GAP_MIN = 0.10  # ahead of the best match of any other number by at least this much
DIST_SCALE = 8.0  # mean distance (pixels of GLYPH, city block) that scores 0
FONTS = (
    cv2.FONT_HERSHEY_SIMPLEX,
    cv2.FONT_HERSHEY_DUPLEX,
    cv2.FONT_HERSHEY_COMPLEX,
    cv2.FONT_HERSHEY_TRIPLEX,
    cv2.FONT_HERSHEY_SCRIPT_SIMPLEX,
    cv2.FONT_HERSHEY_SCRIPT_COMPLEX,
)


def _shrink(mask, nh, nw):
    """A bool mask shrunk to nh x nw by counting: a pixel is ink when a third of its block is."""
    h, w = mask.shape
    c = np.zeros((h + 1, w + 1), np.int64)
    c[1:, 1:] = np.cumsum(np.cumsum(mask.astype(np.int64), 0), 1)
    ys = (np.arange(nh + 1) * h) // nh
    xs = (np.arange(nw + 1) * w) // nw
    s = (
        c[ys[1:, None], xs[None, 1:]]
        - c[ys[:-1, None], xs[None, 1:]]
        - c[ys[1:, None], xs[None, :-1]]
        + c[ys[:-1, None], xs[None, :-1]]
    )
    area = (ys[1:] - ys[:-1])[:, None] * (xs[1:] - xs[:-1])[None, :]
    return 3 * s >= np.maximum(area, 1)


def _fit(mask):
    """The ink's bounding box, shrunk to fit GLYPH x GLYPH (keeping its shape) and centred; None if empty."""
    ys, xs = np.nonzero(mask)
    if len(ys) == 0:
        return None
    m = mask[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]
    h, w = m.shape
    big = max(h, w)
    nh, nw = (
        max(1, (h * GLYPH + big // 2) // big),
        max(1, (w * GLYPH + big // 2) // big),
    )
    if (
        h < nh or w < nw
    ):  # small ink: grow it first (nearest), so shrinking never has empty blocks
        f = -(-GLYPH // min(h, w))
        m = np.repeat(np.repeat(m, f, 0), f, 1)
    out = np.zeros((GLYPH, GLYPH), bool)
    y0, x0 = (GLYPH - nh) // 2, (GLYPH - nw) // 2
    out[y0 : y0 + nh, x0 : x0 + nw] = _shrink(m, nh, nw)
    return out


GLYPHS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cube_glyphs.png")


def _templates():
    """(value index, shape) for each number in each font: the Hershey fonts plain and bold, upright
    and slanted, and the fonts in cube_glyphs.png (one row of GLYPH squares per font)."""
    out = []
    sheet = cv2.imread(GLYPHS, cv2.IMREAD_GRAYSCALE) > 127
    for r in range(sheet.shape[0] // GLYPH):
        for vi in range(len(VALUES)):
            out.append(
                (vi, sheet[r * GLYPH : (r + 1) * GLYPH, vi * GLYPH : (vi + 1) * GLYPH])
            )
    for vi, v in enumerate(VALUES):
        for font in FONTS:
            for italic in (0, cv2.FONT_ITALIC):
                for thick in (3, 7):
                    img = np.zeros((200, 360), np.uint8)
                    cv2.putText(
                        img, str(v), (20, 150), font | italic, 4, 255, thick, cv2.LINE_8
                    )
                    out.append((vi, _fit(img > 0)))
    return np.int64([vi for vi, _ in out]), np.stack([t for _, t in out])


def thin(mask):
    """The strokes of a bool mask thinned to one pixel (Zhang and Suen), in integers."""
    m = np.pad(mask.astype(np.uint8), 1)
    while True:
        changed = False
        for step in (0, 1):
            p2, p3, p4 = m[:-2, 1:-1], m[:-2, 2:], m[1:-1, 2:]
            p5, p6, p7 = m[2:, 2:], m[2:, 1:-1], m[2:, :-2]
            p8, p9 = m[1:-1, :-2], m[:-2, :-2]
            nb = [p2, p3, p4, p5, p6, p7, p8, p9]
            b = sum(x.astype(np.int32) for x in nb)
            a = sum(
                ((nb[i] == 0) & (nb[(i + 1) % 8] == 1)).astype(np.int32)
                for i in range(8)
            )
            if step == 0:
                c = (p2 * p4 * p6 == 0) & (p4 * p6 * p8 == 0)
            else:
                c = (p2 * p4 * p8 == 0) & (p2 * p6 * p8 == 0)
            drop = (m[1:-1, 1:-1] == 1) & (b >= 2) & (b <= 6) & (a == 1) & c
            if drop.any():
                m[1:-1, 1:-1][drop] = 0
                changed = True
        if not changed:
            return m[1:-1, 1:-1] > 0


def _dist(skel):
    """City-block distance of every pixel to the nearest stroke pixel (whole numbers)."""
    return cv2.distanceTransform((~skel).astype(np.uint8), cv2.DIST_L1, 3).astype(
        np.int64
    )


_T_VALUE, _T_SHAPE = _templates()
_T_SKEL = np.stack([thin(t) for t in _T_SHAPE])
_T_DIST = np.stack([_dist(t) for t in _T_SKEL])
_T_COUNT = _T_SKEL.reshape(len(_T_SKEL), -1).sum(1)


def _scores(glyph):
    """How well glyph matches each template: 1 - the mean distance between their thinned strokes
    (each way, the larger of the two) / DIST_SCALE, so a thick or thin font of the same number still
    matches and a blot matches nothing."""
    skel = thin(glyph)
    n = int(skel.sum())
    if n == 0:
        return np.zeros(len(_T_SKEL))
    a = _T_DIST[:, skel].sum(1) / n  # the glyph's strokes to the template's
    b = (_dist(skel)[None] * _T_SKEL).reshape(len(_T_SKEL), -1).sum(
        1
    ) / _T_COUNT  # and back
    return 1 - np.maximum(a, b) / DIST_SCALE


def face(gray, x, y, side, ang):
    """The face (centre x, y, side, angle in degrees of one side) cut out of gray, FACE x FACE, upright
    to within a quarter turn."""
    t = math.radians(ang)
    c, s = exact.snap(math.cos(t), 2.0**-24), exact.snap(math.sin(t), 2.0**-24)
    k = exact.snap(FACE / (side * INNER), 2.0**-24)
    h = FACE / 2
    # the face's centre to the middle of the output, turned by -ang and scaled by k
    M = [
        [k * c, k * s, h - k * (c * x + s * y)],
        [-k * s, k * c, h - k * (-s * x + c * y)],
        [0.0, 0.0, 1.0],
    ]
    M = [[exact.snap(v, 2.0**-20) for v in row] for row in M]
    return exact.warp(gray, M, (FACE, FACE))


def ink(f):
    """The marks on a face: the pixels on the far side of Otsu's threshold from the face itself,
    without what lies mostly along the edge (the bevel, a shadow, the board beyond; a number may
    reach the edge). None if too little or too much."""
    t, _ = cv2.threshold(f, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    light = f > t
    m = FACE // 6
    centre = light[m:-m, m:-m]
    # the face is what most of it is (the ink is the smaller part)
    mask = ~light if 2 * int(centre.sum()) > centre.size else light
    n, lab, st, _ = cv2.connectedComponentsWithStats(
        mask.astype(np.uint8), connectivity=8
    )
    r = int(RING * FACE)
    ring = np.ones((FACE, FACE), bool)
    ring[r:-r, r:-r] = False
    in_ring = np.bincount(lab[ring], minlength=n)
    keep = np.zeros(n, bool)
    for i in range(1, n):
        a = st[i, cv2.CC_STAT_AREA]
        if a < 0.004 * FACE * FACE or 2 * in_ring[i] > a:  # specks, and the edge
            continue
        keep[i] = True
    out = keep[lab]
    share = out.sum() / (FACE * FACE)
    if not INK_MIN <= share <= INK_MAX:
        return None
    return out


def read(gray, x, y, side, ang):
    """The number on the face, its score and the best other number's score: (value or None, best, other)."""
    m = ink(face(gray, x, y, side, ang))
    if m is None:
        return None, 0.0, 0.0
    best = np.zeros(len(VALUES))
    for r in range(4):
        g = _fit(np.rot90(m, r))
        if g is None:
            continue
        sc = _scores(g)
        for vi in range(len(VALUES)):
            best[vi] = max(best[vi], float(sc[_T_VALUE == vi].max()))
    order = np.argsort(-best, kind="stable")
    top, second = float(best[order[0]]), float(best[order[1]])
    value = VALUES[order[0]] if top >= SCORE_MIN and top - second >= GAP_MIN else None
    return value, top, second
