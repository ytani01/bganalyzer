"""Find the doubling cube: a square block bigger than a die, with a number on it instead of pips.

Works like dice.py, on the board seen from straight above, but looks a little beyond the playing
area too (the cube often waits on the frame or by the side of the board).
Says where the cube lies: in the middle (no one owns it), or on 手前's (white) or 奥's (black) side.
The number on it is not read.
"""
from __future__ import annotations

import cv2
import numpy as np

import dice as dice_reader

SIDE_MIN, SIDE_MAX = 0.45, 1.15    # cube side / checker diameter
MARGIN = 2.2                       # how far (checker diameters) to look beyond the playing area, left and right
MIN_READINGS = 6                   # brightness levels at which the block is found
MIDDLE = 0.18                      # within this share of the board's height from the middle line: in the middle


def _ink(gray, body):
    """Share of the face covered by marks clearly darker or lighter than it, and how many marks."""
    s = body["side"]
    x, y, w, h = cv2.boundingRect(body["hull"])
    roi = gray[y:y + h, x:x + w]
    mask = np.zeros(roi.shape, np.uint8)
    cv2.drawContours(mask, [body["hull"] - (x, y)], -1, 255, -1)
    mask = cv2.erode(mask, np.ones((3, 3), np.uint8), iterations=max(1, int(s * 0.08)))
    if cv2.countNonZero(mask) < 30:
        return 0.0, 0
    best = (0.0, 0)
    for dark in (True, False):
        ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(s * 0.35) | 1,) * 2)
        hat = cv2.morphologyEx(roi, cv2.MORPH_BLACKHAT if dark else cv2.MORPH_TOPHAT, ker)
        if np.percentile(hat[mask > 0], 99) < 50:
            continue
        spot = ((hat > 0.5 * np.percentile(hat[mask > 0], 99)) & (mask > 0)).astype(np.uint8)
        n, _, st, _ = cv2.connectedComponentsWithStats(spot)
        marks = [a for a in st[1:, cv2.CC_STAT_AREA] if a >= 0.003 * s * s]
        share = sum(marks) / cv2.countNonZero(mask)
        if share > best[0]:
            best = (share, len(marks))
    return best


def read_cube(img, H, lay, pitch: float, circles=(), dice=(), debug=None):
    """The cube near the board, or None. H maps board.py's canonical board (no margin) to the photo.

    Returns dict(at="centre" | "white" | "black", x, y, side) in canonical coordinates."""
    corners = cv2.perspectiveTransform(lay.src_pts()[None], H)[0]
    k = float(np.clip(np.sqrt(cv2.contourArea(corners) / (lay.w * lay.h)), 1, max(1.0, dice_reader.WORK_PITCH / pitch)))
    mx = MARGIN * pitch
    size = (int((lay.w + 2 * mx) * k), int(lay.h * k))
    S = np.array([[k, 0, k * mx], [0, k, 0], [0, 0, 1]], np.float64)
    ground = cv2.warpPerspective(img, S @ np.linalg.inv(H), size, flags=cv2.INTER_AREA)
    gray = cv2.cvtColor(ground, cv2.COLOR_BGR2GRAY)
    # the part of the view that is in the photo (outside it the warp is black, and its edge a "square")
    inside = cv2.warpPerspective(np.full(img.shape[:2], 255, np.uint8), S @ np.linalg.inv(H), size, flags=cv2.INTER_NEAREST)
    inside = cv2.erode(inside, np.ones((3, 3), np.uint8), iterations=3)
    inside[:3], inside[-3:], inside[:, :3], inside[:, -3:] = 0, 0, 0, 0

    def in_view(b):
        x, y, w, h = cv2.boundingRect(b["hull"])
        return bool(inside[y:y + h, x:x + w].all())

    bodies = [b for b in dice_reader._bodies(gray, pitch * k)
              if SIDE_MIN * pitch * k <= b["side"] <= SIDE_MAX * pitch * k and in_view(b)]
    found = []
    for b in bodies:
        x, y = b["x"] / k - mx, b["y"] / k
        # not a checker (a stack's checkers can make a square), not a die read by dice.py.
        # (A cube can be taken for a checker too: then the circle is a little smaller than the square.)
        if any(np.hypot(x - c[0], y - c[1]) < c[2] and c[2] > 0.47 * b["side"] / k for c in circles):
            continue
        if any(d["sure"] and np.hypot(x - d["x"], y - d["y"]) < 0.6 * d["side"] for d in dice):
            continue
        # a die: its pips sit like a face
        if any(dice_reader._face_value(dice_reader._pips(gray, b, dark, 0.5), b) for dark in (True, False)):
            continue
        share, marks = _ink(gray, b)
        if not (0.04 <= share <= 0.4 and 1 <= marks <= 4):
            continue
        found.append(b | dict(cx=x, cy=y))
    cubes = []
    for b in sorted(found, key=lambda b: -b["side"]):
        if any(np.hypot(b["cx"] - c["x"], b["cy"] - c["y"]) < 0.6 * c["side"] for c in cubes):
            continue
        seen = [o for o in found if np.hypot(b["cx"] - o["cx"], b["cy"] - o["cy"]) < 0.5 * b["side"] / k]
        cubes.append(dict(x=round(float(b["cx"]), 1), y=round(float(b["cy"]), 1),
                          side=round(float(b["side"] / k), 1), seen=len(seen)))
    if debug is not None:
        g = ground.copy()
        for b in found:
            cv2.drawContours(g, [b["hull"]], -1, (0, 255, 255), 1)
        cv2.imwrite(debug, g)
    sure = [c for c in cubes if c["seen"] >= MIN_READINGS]
    if len(sure) != 1:
        return None
    c = sure[0]
    off = c["y"] / lay.h - 0.5
    at = "centre" if abs(off) < MIDDLE else "white" if off > 0 else "black"
    return dict(at=at, x=c["x"], y=c["y"], side=c["side"])
