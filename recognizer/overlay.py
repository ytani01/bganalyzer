"""What the recognizer found, in the photo's pixels, for the app's reading overlay (info["geometry"] and
the stages recognize reports as it goes); and debug images of the canonical board."""

from __future__ import annotations

import cv2
import numpy as np

import exact
from colours import LAB_W


def geometry_frame(H, lay):
    """Where the playing area and its columns are: corners in image pixels (TL TR BR BL), columns and
    bar edges as fractions of the width."""
    return dict(
        corners=exact.apply_h(H, lay.src_pts()).round(1).tolist(),
        columns=[round(float(lay.col_x(c) / lay.w), 4) for c in range(12)],
        bar=[
            round(float(lay.a / lay.w), 4),
            round(float((lay.a + lay.bar) / lay.w), 4),
        ],
    )


def geometry_counts(runs, bar, bottom_colour, lay, H):
    """The checkers counted on each point and on the bar, [{"at": [x, y], "n": n, "side": "white" | "black"}, ...],
    "at" in image pixels just outside the playing area by the point (on the bar for the bar), for the
    app's reading overlay."""
    off = 0.35 * lay.pw
    marks = [
        (lay.col_x(c), -off if row == "top" else lay.h + off, n, k)
        for (c, row), (k, n) in sorted(runs.items())
        if n and k is not None
    ]
    mid = lay.a + lay.bar / 2
    marks += [
        (mid, lay.h * (0.62 if k == bottom_colour else 0.38), n, k)
        for k, n in enumerate(bar)
        if n
    ]
    if not marks:
        return []
    pts = cv2.perspectiveTransform(np.float32([[x, y] for x, y, *_ in marks])[None], H)[
        0
    ]
    return [
        dict(
            at=[round(float(x), 1), round(float(y), 1)],
            n=int(n),
            side="white" if k == bottom_colour else "black",
        )
        for (x, y), (_, _, n, k) in zip(pts, marks)
    ]


def geometry_tips(tips, H):
    """The triangle tips found, in image pixels [[x, y], ...] (for the app's reading overlay)."""
    if not tips:
        return []
    pts = np.float32([[t[2], t[3]] for t in tips])
    return (
        cv2.perspectiveTransform(pts[None], H)[0].astype(np.float64).round(1).tolist()
    )


def geometry_square(d, H):
    """A die or the cube (x, y, side in canonical coordinates) as its square in image pixels,
    [[x, y] TL TR BR BL] (for the app's reading overlay)."""
    x, y, h = d["x"], d["y"], d["side"] / 2
    pts = np.float32([[x - h, y - h], [x + h, y - h], [x + h, y + h], [x - h, y + h]])
    return (
        cv2.perspectiveTransform(pts[None], H)[0].astype(np.float64).round(1).tolist()
    )


def geometry_checkers(circles, cc, bottom_colour, H):
    """The checker circles found, in image pixels [[x, y, r, side], ...], side "white" (手前) or "black"
    by the nearer checker colour (for the app's reading overlay; the counts do not come from this)."""
    if not len(circles):
        return []
    pts = np.float32(
        [[x, y] for x, y, *_ in circles] + [[x + r, y] for x, y, r, *_ in circles]
    )
    img = cv2.perspectiveTransform(pts[None], H)[0]
    n = len(circles)
    out = []
    for i, (_, _, _, lab, _) in enumerate(circles):
        k = (
            bottom_colour
            if cc is None
            else int(
                np.argmin(
                    np.linalg.norm((np.float32(cc) - np.float32(lab)) * LAB_W, axis=1)
                )
            )
        )
        r = float(np.linalg.norm(img[n + i] - img[i]))
        out.append(
            [
                round(float(img[i][0]), 1),
                round(float(img[i][1]), 1),
                round(r, 1),
                "white" if k == bottom_colour else "black",
            ]
        )
    return out


def save_debug(prefix, ground, lay, m, runs, tips, circles=()):
    g = ground.copy()
    for c, r, x, y, *_ in tips:
        cv2.circle(g, (int(x + m), int(y + m)), 6, (0, 255, 0), 2)
    for c in range(12):
        cv2.line(
            g,
            (int(m + lay.col_x(c)), 0),
            (int(m + lay.col_x(c)), g.shape[0]),
            (255, 0, 0),
            1,
        )
    cv2.imwrite(prefix + "_geometry.jpg", g)
    over = ground.copy()
    for x, y, r, *_ in circles:
        cv2.circle(over, (int(x + m), int(y + m)), int(r), (0, 255, 0), 3)
    for (c, row), (col, n) in runs.items():
        cx = int(m + lay.col_x(c))
        cv2.line(over, (cx, m), (cx, int(m + lay.h)), (0, 255, 0), 1)
        y = m + 25 if row == "top" else int(m + lay.h - 10)
        if n:
            cv2.putText(over, f"{n}{'AB'[col]}", (cx - 22, y), 0, 0.9, (0, 0, 0), 4)
            cv2.putText(
                over, f"{n}{'AB'[col]}", (cx - 22, y), 0, 0.9, (255, 255, 255), 2
            )
    cv2.imwrite(prefix + "_checkers.jpg", over)
