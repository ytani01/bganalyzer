"""Read the two dice lying in the playing area, when they can be read with confidence.

Works on the board seen from straight above (as in board.py, at the photo's resolution):
  1. Die bodies: square blobs of a die's size, at every brightness level.
  2. Pips: small round spots inside a body, clearly darker (or lighter) than its face.
  3. The pips must form a die face (1..6), lined up with the body's sides.
  4. A die is found again and again at different levels; a place read often and alike is sure.
The result is only given when exactly two sure dice lie in the fields, alike in colour and size
(one die, dice on the bar, and a second pair of dice leave it unread).
When that leaves the dice unread, they are looked for again from the pips alone (in an oblique
photo a die's sides add to its top face and no square shows; TODO-079).
"""

from __future__ import annotations

import itertools
import math

import cv2
import numpy as np

import exact

SIDE_MIN, SIDE_MAX = 0.28, 1.1  # die side / checker diameter
WORK_PITCH = 120  # checker diameter (px) to look for dice at
PIP_CONTRAST = 30  # a pip against the face (grey levels)
MIN_READINGS = 4  # a die is seen at several brightness levels; a pattern that looks like one, rarely


def _bodies(gray, pitch):
    """Square blobs of a die's size, lighter or darker than around them, at any brightness level.

    Returns dicts with the centre, side and outline (convex hull)."""
    smin, smax = SIDE_MIN * pitch, SIDE_MAX * pitch
    small = np.ones((3, 3), np.uint8)
    out = []
    for t in range(16, 250, 8):
        for light in (True, False):
            bw = ((gray > t) if light else (gray < t)).astype(np.uint8)
            bw = cv2.morphologyEx(bw, cv2.MORPH_OPEN, small)
            n, lab, st, _ = cv2.connectedComponentsWithStats(bw)
            # the blobs of a die's size and area, picked out all at once (TODO-173)
            big = np.maximum(st[:, 2], st[:, 3])
            ok = (
                (0.7 * smin <= big)
                & (big <= 1.45 * smax)
                & (st[:, 4] >= 0.4 * smin * smin)
            )
            ok[0] = False  # the background
            for i in np.flatnonzero(ok):
                x, y, w, h, a = st[i]
                pts = cv2.findNonZero(
                    (lab[y : y + h, x : x + w] == i).astype(np.uint8)
                ) + (x, y)
                hull = cv2.convexHull(pts)
                # (not cv2.minAreaRect: it works in floats and gives other boxes on other CPUs)
                (cx, cy), (rw, rh), ang = exact.min_area_rect(hull)
                side = (rw + rh) / 2
                if not smin <= side <= smax or max(rw, rh) > 1.3 * min(rw, rh):
                    continue
                if (
                    cv2.contourArea(hull) < 0.86 * rw * rh
                ):  # a square fills its box; a circle 0.79
                    continue
                # four corners (a checker with something next to it can fill its box too)
                if (
                    len(cv2.approxPolyDP(hull, 0.05 * cv2.arcLength(hull, True), True))
                    != 4
                ):
                    continue
                out.append(dict(x=cx, y=cy, side=side, ang=ang, hull=hull))
    return out


def _pips_level(gray, body, dark: bool, f: float = 0.5):
    """Like _pips, but cut at one brightness level between the face and the pips."""
    s = body["side"]
    x, y, w, h = cv2.boundingRect(body["hull"])
    roi = gray[y : y + h, x : x + w]
    mask = np.zeros(roi.shape, np.uint8)
    cv2.drawContours(mask, [body["hull"] - (x, y)], -1, 255, -1)
    mask = cv2.erode(mask, np.ones((3, 3), np.uint8), iterations=max(1, int(s * 0.04)))
    if cv2.countNonZero(mask) < 20:
        return []
    vals = roi[mask > 0].astype(np.float32)
    face = np.percentile(vals, 75 if dark else 25)
    pip_lv = np.percentile(vals, 2 if dark else 98)
    if abs(face - pip_lv) < 40:
        return []
    thr = face + f * (pip_lv - face)
    spot = (((roi < thr) if dark else (roi > thr)) & (mask > 0)).astype(np.uint8)
    return _spots(spot, s, x, y, roi, mask, dark)


def _spots(spot, s, x0, y0, roi, mask, dark):
    """Round spots of a pip's size in a binary image, clearly darker (or lighter) than most of the
    face: list of (x, y, area)."""
    face = np.median(roi[mask > 0])
    n, lab, st, cen = cv2.connectedComponentsWithStats(spot)
    out = []
    for i in range(1, n):
        a = st[i, cv2.CC_STAT_AREA]
        w, h = st[i, cv2.CC_STAT_WIDTH], st[i, cv2.CC_STAT_HEIGHT]
        if not (0.004 * s * s <= a <= 0.06 * s * s):
            continue
        if max(w, h) > 2.0 * min(w, h) or a < 0.45 * w * h:
            continue
        # (not the bits of face between dark pips)
        if (face - roi[lab == i].mean()) * (1 if dark else -1) < PIP_CONTRAST:
            continue
        out.append((float(cen[i][0] + x0), float(cen[i][1] + y0), float(a)))
    # the pips of one face are the same size; smaller ones are on the sides (or noise)
    if out:
        big = max(a for *_, a in out)
        out = [p for p in out if p[2] >= 0.4 * big]
    return out


def _pips(gray, body, dark: bool, f: float = 0.5):
    """Spots darker (or lighter) than the face around them, inside the body: list of (x, y, area).

    Measured against the local face (top-hat), so glare across a glossy face does not matter.
    f: the cut, as a share of the strongest spot's contrast."""
    s = body["side"]
    x, y, w, h = cv2.boundingRect(body["hull"])
    pad = int(s * 0.2) + 2
    x0, y0 = max(x - pad, 0), max(y - pad, 0)
    roi = gray[y0 : y + h + pad, x0 : x + w + pad]
    mask = np.zeros(roi.shape, np.uint8)
    cv2.drawContours(mask, [body["hull"] - (x0, y0)], -1, 255, -1)
    mask = cv2.erode(mask, np.ones((3, 3), np.uint8), iterations=max(1, int(s * 0.04)))
    if cv2.countNonZero(mask) < 20:
        return []
    ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(s * 0.3) | 1,) * 2)
    hat = cv2.morphologyEx(roi, cv2.MORPH_BLACKHAT if dark else cv2.MORPH_TOPHAT, ker)
    top = np.percentile(hat[mask > 0], 99.5)
    if top < 40:  # no contrast inside: no pips (or a plain square)
        return []
    spot = ((hat > f * top) & (mask > 0)).astype(np.uint8)
    return _spots(spot, s, x0, y0, roi, mask, dark)


def _pip_found(gray, pitch, k, lay, circles):
    """Readings of dice found from their pips alone, for dice that show as no square (seen from
    the side in an oblique photo, the sides add to the top face; a clear die's sides are as
    bright as its top). Like _found's readings: one per place and cut (TODO-079).

    Every face has its centre on a pip (1, 3, 5) or halfway between two pips (2, 4, 6): squares
    there, turned along the pair and sized from its spread, are tried. pitch: canonical."""
    P = pitch * k
    smin, smax = SIDE_MIN * P, SIDE_MAX * P
    # not on the bar
    x0, x1 = int((lay.a - 0.1 * pitch) * k), int((lay.a + lay.bar + 0.1 * pitch) * k)
    found = []
    # small dice have their pips only a few pixels apart: against a small neighbourhood too
    for dark, size in itertools.product((False, True), (0.1, 0.25)):
        ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(P * size) | 1,) * 2)
        hat = cv2.morphologyEx(
            gray, cv2.MORPH_BLACKHAT if dark else cv2.MORPH_TOPHAT, ker
        )
        hat[:, max(x0, 0) : max(x1, 0)] = 0
        # pips close together on a light face run into one at a low cut: a die is read at
        # several cuts, a chance pattern at few
        for cut in range(2 * PIP_CONTRAST, 200, PIP_CONTRAST // 2):
            n, _, st, cen = cv2.connectedComponentsWithStats(
                (hat > cut).astype(np.uint8)
            )
            a, w, h = (
                st[:, cv2.CC_STAT_AREA],
                st[:, cv2.CC_STAT_WIDTH],
                st[:, cv2.CC_STAT_HEIGHT],
            )
            ok = (
                (a >= 0.004 * smin * smin)
                & (a <= 0.06 * smax * smax)
                & (np.maximum(w, h) <= 2.0 * np.minimum(w, h))
                & (a >= 0.45 * w * h)
            )
            ok[0] = False
            p, ar = cen[ok], a[ok].astype(np.float64)
            dist = np.sqrt(((p[:, None] - p[None]) ** 2).sum(2))
            # pips of one face: the same size, no further apart than a big die's corners
            pair = (dist >= 0.1 * smin) & (dist <= 0.85 * smax)
            pair &= np.maximum(ar[:, None], ar[None]) <= 2.5 * np.minimum(
                ar[:, None], ar[None]
            )
            around = [np.flatnonzero(r <= 1.2 * smax) for r in dist]
            here = []
            for i, j in zip(*np.nonzero(np.triu(pair))):
                dx, dy = p[j] - p[i]
                d = dist[i, j]
                ang = math.degrees(math.atan2(dy, dx))
                # halfway: two corners across (2..6) or the middle pair of a six; at a pip:
                # a neighbour on the diagonal (3, 5)
                for c, s, t in (
                    ((p[i] + p[j]) / 2, d / 0.85, ang - 45),
                    ((p[i] + p[j]) / 2, d / 0.6, ang),
                    (p[i], d / 0.42, ang - 45),
                    (p[j], d / 0.42, ang - 45),
                ):
                    # a pip is a fair share of the face (not two specks on a big square)
                    lo, hi = sorted((ar[i], ar[j]))
                    if (
                        not smin <= s <= smax
                        or not 0.02 * s * s <= lo <= hi <= 0.08 * s * s
                    ):
                        continue
                    cs, sn = math.cos(math.radians(t)), math.sin(math.radians(t))
                    q = p[around[i]] - c
                    u, v = q[:, 0] * cs + q[:, 1] * sn, -q[:, 0] * sn + q[:, 1] * cs
                    m = around[i][(np.abs(u) < 0.5 * s) & (np.abs(v) < 0.5 * s)]
                    body = dict(x=float(c[0]), y=float(c[1]), side=s, ang=t)
                    val = _face_value([(*p[o], ar[o]) for o in m], body)
                    if val is None or _on_checker(body, val, circles, k):
                        continue
                    box = cv2.boxPoints(((body["x"], body["y"]), (s, s), t))
                    if box.min() < 0 or (box.max(0) >= gray.shape[::-1]).any():
                        continue
                    body["hull"] = np.int32(np.round(box)).reshape(-1, 1, 2)
                    # and the pips found inside the square as in a body read the same face
                    # (not two spots far apart on the board)
                    if not any(
                        _face_value(find(gray, body, dark, 0.5), body) == val
                        for find in (_pips, _pips_level)
                    ):
                        continue
                    here.append(body | dict(value=val, dark_pips=dark))
            # one reading per place at this cut: the face with the most pips (two pips of a
            # six also sit like a small two)
            here.sort(key=lambda b: (-b["value"], -b["side"]))
            kept = []
            for b in here:
                if all(
                    exact.hypot(b["x"] - o["x"], b["y"] - o["y"]) >= 0.6 * o["side"]
                    for o in kept
                ):
                    kept.append(b)
            found += kept
    return found


def _on_checker(b, v, circles, k):
    """A checker's dimple reads as a one (with a bit of a triangle next to it making a square)
    and a pattern on a checker (an engraved flower) can look like a small die."""
    return any(
        v == 1 or b["side"] / k < 1.6 * c[2]
        for c in circles
        if exact.hypot(b["x"] / k - c[0], b["y"] / k - c[1]) < 0.5 * c[2]
    )


# pip layouts in face units (-1..1), in a frame aligned with the die
_LAYOUT = {
    1: [(0, 0)],
    2: [(-1, -1), (1, 1)],
    3: [(-1, -1), (0, 0), (1, 1)],
    4: [(-1, -1), (1, -1), (-1, 1), (1, 1)],
    5: [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)],
    6: [(-1, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (1, 1)],
}


def _face_value(pips, body):
    """The number on the die if the pips sit like a die face, else None."""
    n = len(pips)
    if not 1 <= n <= 6:
        return None
    p = np.float64([(x, y) for x, y, _ in pips])
    c = p.sum(0) / n
    s = body["side"]
    if exact.hypot(c[0] - body["x"], c[1] - body["y"]) > 0.3 * s:
        return None
    if n == 1:
        return 1
    # fit the layout: try rotations, scale from the spread
    best = None
    # the pips run along the die's sides
    for deg in range(-15, 16, 3):
        t = math.radians(body["ang"] + deg)
        # libm's cos and sin may differ in the last bit by CPU: snapped; the product by hand (not BLAS)
        cs, sn = exact.snap(math.cos(t), 2.0**-40), exact.snap(math.sin(t), 2.0**-40)
        dx, dy = p[:, 0] - c[0], p[:, 1] - c[1]
        q = np.stack([dx * cs + dy * sn, -dx * sn + dy * cs], 1)
        # each axis scaled on its own: in small or tilted dice the pips are not quite square
        half = np.abs(q).max(0)
        if (
            half.max() < 0.15 * s
            or half.max() > 0.42 * s
            or half.min() < 0.55 * half.max()
        ):
            continue
        q = q / half
        for ref in (
            np.float64(_LAYOUT[n]),
            np.float64(_LAYOUT[n])[:, ::-1] * (1, -1),
        ):  # and turned by 90°
            # each pip to its nearest layout spot, one to one
            d = np.linalg.norm(q[:, None] - ref[None], axis=2)
            if len(set(d.argmin(1))) < n:
                continue
            err = float(d.min(1).max())
            if best is None or err < best:
                best = err
    if best is None or best > 0.35:
        return None
    return n


def read_dice(img, H, lay, pitch: float, circles=(), debug=None):
    """Dice in the two fields. H maps board.py's canonical board (no margin) to the photo;
    circles are the checkers found there (x, y, r, ...).

    The fields are warped again, at the photo's own resolution (dice pips are only a few pixels).
    Returns dict(values=[high, low] or None, dice=[dict(x, y, side, value, sure, on_bar)...]),
    positions in canonical coordinates."""
    corners = exact.apply_h(H, lay.src_pts())
    # no finer than the photo, and no finer than needed (a checker WORK_PITCH pixels wide)
    k = exact.snap(
        np.clip(
            math.sqrt(exact.polygon_area(corners) / (lay.w * lay.h)),
            1,
            max(1.0, WORK_PITCH / pitch),
        ),
        2.0**-20,
    )
    size = (int(lay.w * k), int(lay.h * k))
    ground = exact.warp(img, exact.mul3(np.diag([k, k, 1.0]), exact.inv3(H)), size)
    gray = cv2.cvtColor(ground, cv2.COLOR_BGR2GRAY)
    lab = cv2.cvtColor(ground, cv2.COLOR_BGR2Lab)
    found = _found(gray, _bodies(gray, pitch * k), circles, k)
    dice, values, out = _read(gray, lab, found, k, lay, pitch)
    field = sum(d["sure"] and not o["on_bar"] for d, o in zip(dice, out))
    if values is None and field < 2:
        # dice seen from the side (an oblique photo) are no square: found from their pips;
        # used only when they make the two dice (TODO-079). Not when two or more were found
        # and not read (both players' dice on the board): the pips would miss a 1 and could
        # pick one pair out of the two
        # (a clear die takes some colour from what lies under it and from the light: the
        # squares placed from the pips take a less even sample, so the colours may differ more)
        pip_found = _pip_found(gray, pitch, k, lay, circles)
        more = _read(gray, lab, pip_found, k, lay, pitch, hue=25)
        if more[1] is not None:
            found, (dice, values, out) = pip_found, more
    if debug is not None:
        g = ground.copy()
        for b in found:
            cv2.drawContours(g, [b["hull"]], -1, (0, 255, 255), 1)
        for d in dice:
            cv2.putText(
                g,
                str(d["value"]) + ("" if d["sure"] else "?"),
                (int(d["x"]), int(d["y"] - d["side"] * 0.7)),
                0,
                1.2,
                (0, 0, 255),
                3,
            )
        cv2.imwrite(debug, g)
    return dict(values=values, dice=out)


def _found(gray, bodies, circles, k):
    """The readings of the bodies: one per way of finding the pips that reads a face."""
    found = []
    for b in bodies:
        # dark pips on a light face, or light pips on a dark one; each way of finding the pips
        # is one reading (the readings of one place are counted below)
        reads = [
            (v, dark)
            for dark in (True, False)
            for find in (_pips, _pips_level)
            for f in (0.35, 0.5, 0.65)
            if (v := _face_value(find(gray, b, dark, f), b))
        ]
        if len({dark for _, dark in reads}) != 1:
            continue
        v = max({v for v, _ in reads}, key=[v for v, _ in reads].count)
        dark = reads[0][1]
        if _on_checker(b, v, circles, k):
            continue
        found += [b | dict(value=v, dark_pips=dark) for v, _ in reads]
    return found


def _read(gray, lab, found, k, lay, pitch, hue=15):
    """The dice of some readings: (dice in ground pixels, values or None, dice for the result).

    hue: how far apart the two dice's colours (Lab a, b) may be."""
    # a real die is found at several brightness levels, nearly always with the same number:
    # one die per place, sure when most readings there agree
    dice = []
    for b in sorted(found, key=lambda b: -b["side"]):
        if any(
            exact.hypot(b["x"] - d["x"], b["y"] - d["y"]) < 0.6 * d["side"]
            for d in dice
        ):
            continue
        seen = [
            o["value"]
            for o in found
            if exact.hypot(b["x"] - o["x"], b["y"] - o["y"]) < 0.6 * b["side"]
        ]
        value = max(set(seen), key=seen.count)
        mask = np.zeros(gray.shape, np.uint8)
        cv2.drawContours(mask, [b["hull"]], -1, 255, -1)
        dice.append(
            b
            | dict(
                value=value,
                seen=seen,
                sure=len(seen) >= MIN_READINGS
                and seen.count(value) >= 0.75 * len(seen),
                lab=np.median(lab[mask > 0], 0).astype(float),
            )
        )
    out = []
    for d in dice:
        x, y = d["x"] / k, d["y"] / k
        out.append(
            dict(
                x=round(x, 1),
                y=round(y, 1),
                side=round(d["side"] / k, 1),
                value=d["value"],
                sure=d["sure"],
                on_bar=bool(lay.a - 0.1 * pitch < x < lay.a + lay.bar + 0.1 * pitch),
            )
        )
    values = None
    field = [(d, o) for d, o in zip(dice, out) if d["sure"] and not o["on_bar"]]
    if len(field) == 2:
        (a, _), (b, _) = field
        if (
            a["dark_pips"] == b["dark_pips"]
            and max(a["side"], b["side"]) < 1.3 * min(a["side"], b["side"])
            and exact.norm(a["lab"][1:] - b["lab"][1:]) < hue
            and abs(a["lab"][0] - b["lab"][0]) < 60
        ):
            values = sorted([a["value"], b["value"]], reverse=True)
    return dice, values, out
