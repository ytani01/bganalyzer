"""The board's colours (step 3 of the pipeline in board.py): plain field, the two triangle colours and the
frame, sampled in the canonical image; and which triangle colour each point has."""
from __future__ import annotations

import cv2
import numpy as np

import exact
from geometry import TRI_DEPTH, Layout, plain_colour

LAB_W = np.float32([0.5, 1.0, 1.0])  # lighting mostly changes L


def board_colours(ground_bgr, lay: Layout, m: int, tips, mask=None):
    """Lab colours of the plain field, the two triangle colours and the frame.

    mask: pixels to ignore (e.g. under checkers already found)."""
    lab = cv2.cvtColor(ground_bgr, cv2.COLOR_BGR2Lab).astype(np.float32)
    plain = plain_colour(lab, lay, m, mask)
    if mask is not None:
        lab = lab.copy()
        lab[mask] = np.nan
    px = []
    for c, r, x, y, L, dx, _ in tips:     # inside detected triangles, along the centre line
        sgn = 1 if r == "top" else -1
        for f in np.linspace(0.15, 0.5, 8):
            yy, xx = int(m + y - sgn * L * f), int(m + x - dx * L * f * sgn)
            px.append(lab[yy - 1:yy + 2, xx - 1:xx + 2].reshape(-1, 3))
    if not px:   # no triangle found: fall back to the band near where tips should be
        for c in range(12):
            x = int(m + lay.col_x(c))
            for y0 in (m + lay.h * TRI_DEPTH * 0.3, m + lay.h * (1 - TRI_DEPTH * 0.6)):
                px.append(lab[int(y0):int(y0 + lay.h * TRI_DEPTH * 0.3), x - 2:x + 3].reshape(-1, 3))
    px = np.vstack(px)
    px = px[~np.isnan(px).any(1)]
    px = px[np.linalg.norm(px - plain, axis=1) > 25] if (np.linalg.norm(px - plain, axis=1) > 25).sum() > 10 else px
    # in integers (Lab of 8-bit pixels are whole numbers): cv2.kmeans differs by CPU
    _, tri = exact.kmeans(px.astype(np.int32), 2)
    # frame: the strip just outside the near (bottom) edge of the field
    frames = [np.nanmedian(lab[int(m + lay.h + m * 0.3):int(m + lay.h + m * 0.8),
                            int(m):int(m + lay.w)].reshape(-1, 3), 0)]
    bx0, bx1 = int(m + lay.col_x(5) + lay.pw * 0.6), int(m + lay.col_x(6) - lay.pw * 0.6)
    if bx1 - bx0 >= 4:   # the bar, where visible
        frames.append(np.nanmedian(lab[int(m + lay.h * 0.3):int(m + lay.h * 0.7), bx0:bx1].reshape(-1, 3), 0))
    for x0 in (int(m * 0.2), int(m + lay.w + m * 0.3)):   # left / right frame
        frames.append(np.nanmedian(lab[int(m + lay.h * 0.3):int(m + lay.h * 0.7), x0:x0 + int(m * 0.5)].reshape(-1, 3), 0))
    frames = [f for f in frames if not np.isnan(f).any()]
    return np.vstack([plain, tri, *frames]).astype(np.float32)


def triangle_colour_map(board, lay, m, tips, ground_lab):
    """Triangle colour index for each (column, row), using alternation."""
    tri = board[1:3] * LAB_W
    votes = []
    for c, r, x, y, L, dx, _ in tips:
        sgn = 1 if r == "top" else -1
        yy, xx = int(m + y - sgn * L * 0.3), int(m + x)
        col = np.median(ground_lab[yy - 2:yy + 3, xx - 2:xx + 3].reshape(-1, 3), 0) * LAB_W
        idx = int(np.argmin(np.linalg.norm(tri - col, axis=1)))
        votes.append((idx - c - (r == "bottom")) % 2)
    off = int(round(np.mean(votes))) if votes else 0
    return {(c, r): (c + (r == "bottom") + off) % 2 for c in range(12) for r in ("top", "bottom")}
