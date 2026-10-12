"""Synthetic board photos with known positions, for regression tests.

Draws a board in the style of the user's board (kraft field, red / navy
triangles, white frame, dark-red / purple checkers), places a random legal
looking position, then views it with a random mild perspective, lighting
gradient, blur and noise. Checkers are drawn flat (no thickness), so this
tests the pipeline on near top-down photos.
"""
from __future__ import annotations

import json
import os
import sys

import cv2
import numpy as np

from position import Position

KRAFT = (150, 195, 228)
RED = (62, 72, 196)
NAVY = (112, 72, 58)
FRAME = (238, 240, 242)
DARK_RED = (48, 36, 132)   # colour 0 in the recogniser is the darker one -> purple below
PURPLE = (104, 44, 92)


def random_position(rng) -> Position:
    p = Position()
    free = list(range(24))
    rng.shuffle(free)
    for sign in (1, -1):
        left = 15
        if rng.random() < 0.2:
            n = int(rng.integers(1, 3))
            if sign > 0:
                p.bar_white = n
            else:
                p.bar_black = n
            left -= n
        while left > 0:
            i = free.pop()
            n = int(min(left, rng.integers(1, 6)))
            p.points[i] = sign * n
            left -= n
    return p


def render_board(p: Position, rng, white_colour=PURPLE, black_colour=DARK_RED, home="right"):
    """Canonical top-down board image and its playing-area corners."""
    pw, h, bar, f = 88, 1000, 70, 70
    a = 6 * pw
    w = 2 * a + bar
    img = np.full((h + 2 * f, w + 2 * f, 3), FRAME, np.uint8)
    for x0 in (f, f + a + bar):
        cv2.rectangle(img, (x0, f), (x0 + a, f + h), KRAFT, -1)
    depth = 0.43 * h

    def col_x(c):
        return f + (c + 0.5) * pw + (bar if c >= 6 else 0)

    for c in range(12):
        for row, (y0, s) in (("top", (f, 1)), ("bottom", (f + h, -1))):
            colour = RED if (c + (row == "bottom")) % 2 == 0 else NAVY
            tri = np.int32([(col_x(c) - pw / 2, y0), (col_x(c) + pw / 2, y0), (col_x(c), y0 + s * depth)])
            cv2.fillConvexPoly(img, tri, colour, lineType=cv2.LINE_AA)
    # paper texture
    tex = rng.normal(0, 4, img.shape[:2]).astype(np.float32)
    img = np.clip(img.astype(np.float32) + tex[..., None], 0, 255).astype(np.uint8)

    r = int(pw * 0.48)

    def checker(x, y, colour):
        cv2.circle(img, (int(x + 4), int(y + 5)), r, (90, 110, 130), -1, cv2.LINE_AA)   # shadow
        cv2.circle(img, (int(x), int(y)), r, tuple(int(v * 0.75) for v in colour), -1, cv2.LINE_AA)
        cv2.circle(img, (int(x), int(y)), int(r * 0.86), colour, -1, cv2.LINE_AA)
        cv2.ellipse(img, (int(x - r * 0.3), int(y - r * 0.35)), (int(r * 0.25), int(r * 0.12)), -30, 0, 360,
                    tuple(min(255, int(v * 1.5) + 30) for v in colour), -1, cv2.LINE_AA)

    for i, n in enumerate(p.points):
        if n == 0:
            continue
        # White point i+1: bottom row right->left = 1..12, top row left->right = 13..24
        pt = i + 1
        if pt <= 12:
            c, row = 12 - pt, "bottom"
        else:
            c, row = pt - 13, "top"
        if home == "left":
            c = 11 - c
        colour = white_colour if n > 0 else black_colour
        step = 2 * r + 2 if abs(n) <= 5 else (h * 0.45 - 2 * r) / (abs(n) - 1)
        for k in range(abs(n)):
            y = f + r + 2 + k * step if row == "top" else f + h - r - 2 - k * step
            checker(col_x(c), y, colour)
    bx = f + a + bar / 2
    for k in range(p.bar_white):
        checker(bx, f + h * 0.6 + k * 2 * r, white_colour)
    for k in range(p.bar_black):
        checker(bx, f + h * 0.4 - k * 2 * r, black_colour)
    corners = np.float32([(f, f), (f + w, f), (f + w, f + h), (f, f + h)])
    return img, corners


def photograph(board, corners, rng, out_size=(3000, 2250), tilt=0.04):
    W, H = out_size
    bh, bw = board.shape[:2]
    scale = 0.75 * min(W / bw, H / bh)
    cx, cy = W / 2 + rng.uniform(-0.05, 0.05) * W, H / 2 + rng.uniform(-0.05, 0.05) * H
    src = np.float32([(0, 0), (bw, 0), (bw, bh), (0, bh)])
    dst = np.float32([(cx + (x - bw / 2) * scale, cy + (y - bh / 2) * scale) for x, y in src])
    dst += rng.uniform(-tilt, tilt, dst.shape).astype(np.float32) * scale * bh
    ang = rng.uniform(-0.15, 0.15)
    R = np.float32([[np.cos(ang), -np.sin(ang)], [np.sin(ang), np.cos(ang)]])
    dst = (dst - (cx, cy)) @ R.T + (cx, cy)
    M = cv2.getPerspectiveTransform(src, dst.astype(np.float32))
    bg = np.full((H, W, 3), (150, 190, 215), np.uint8)
    bg = cv2.add(bg, rng.integers(0, 25, (H, W, 1), dtype=np.uint8).repeat(3, 2))
    bg = cv2.GaussianBlur(bg, (0, 0), 6)
    photo = cv2.warpPerspective(board, M, (W, H), dst=bg, borderMode=cv2.BORDER_TRANSPARENT)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    g = 0.8 + 0.3 * (xx / W * rng.uniform(-1, 1) + yy / H * rng.uniform(-1, 1) + 1) / 2
    photo = np.clip(photo.astype(np.float32) * g[..., None] + rng.normal(0, 4, photo.shape), 0, 255)
    photo = cv2.GaussianBlur(photo.astype(np.uint8), (0, 0), rng.uniform(0.6, 1.6))
    true_corners = cv2.perspectiveTransform(corners[None], M)[0]
    return photo, true_corners


def make(n, out_dir, seed=0):
    os.makedirs(out_dir, exist_ok=True)
    rng = np.random.default_rng(seed)
    for k in range(n):
        p = random_position(rng)
        home = "right" if k % 2 == 0 else "left"
        board, corners = render_board(p, rng, home=home)
        photo, c = photograph(board, corners, rng)
        # rough corners as a person would tap them
        tapped = c + rng.normal(0, 12, c.shape)
        name = f"synth_{k:02d}"
        cv2.imwrite(os.path.join(out_dir, name + ".jpg"), photo, [cv2.IMWRITE_JPEG_QUALITY, 88])
        json.dump({"image": name + ".jpg", "corners_TL_TR_BR_BL": tapped.round(1).tolist(), "home": home,
                   "points": p.points, "bar_white": p.bar_white, "bar_black": p.bar_black,
                   "off_white": 0, "off_black": 0},
                  open(os.path.join(out_dir, name + ".truth.json"), "w"))


if __name__ == "__main__":
    make(int(sys.argv[1]) if len(sys.argv) > 1 else 20, sys.argv[2] if len(sys.argv) > 2 else "synth")
