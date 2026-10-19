"""Photos with a doubling cube of a known number pasted in, for checking cube_value.py (TODO-025).

No sample has a cube showing 4, 8, 16 or 32 on one side, so these are made: the user's own board
photos (photo-blue-red-top, photo-carved-brown-top) with a cube drawn in, lying flat on the board's plane (the board's four
corners give its perspective), at any turn, in the trays or on the frame beside the playing area,
on either player's side, or in a playing field. The numbers are drawn in make_cube_glyphs.TEST_FONTS,
which the reader's templates never use. Writes samples/synth-cube-*.jpg and their .truth.json:

  uv run python recognizer/synth_cube.py      # needs Pillow (a dev dependency) and the fonts
"""

from __future__ import annotations

import json
import math
import os

import cv2
import make_cube_glyphs
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
APP_SIDE = 2048  # the photos are shrunk to the app's upload size
SAMPLES = os.path.join(HERE, "..", "samples")
# (base photo, where the cube's centre goes as (u, v) of the playing area, side): u, v from 0 to 1
# across and down; beyond 0..1 is outside the playing area (a tray, the frame)
SPOTS = {
    "photo-blue-red-top": [
        ((-0.075, 0.82), "white"),
        ((1.06, 0.18), "black"),
        ((0.29, 0.52), "field"),
        ((-0.075, 0.12), "black"),
        ((1.06, 0.88), "white"),
        ((0.70, 0.47), "field"),
    ],
    "photo-carved-brown-top": [
        ((0.30, 0.62), "field"),
        ((0.74, 0.48), "field"),
        ((1.035, 0.80), "white"),
        ((-0.035, 0.22), "black"),
        ((0.88, 0.62), "field"),
        ((1.035, 0.16), "black"),
    ],
}
FACES = [
    ((236, 240, 244), (24, 24, 24)),
    ((214, 232, 240), (30, 30, 30)),
    ((245, 245, 245), (150, 60, 20)),
    ((220, 236, 244), (30, 30, 140)),
    ((40, 40, 40), (235, 235, 235)),
]  # BGR: face, ink


def face_texture(value, font, colours, rng, size=240):
    """A cube's face seen from straight above: the number in the font, bevelled edges, BGR."""
    face, ink_c = colours
    tex = np.zeros((size, size, 3), np.uint8)
    tex[:] = face
    # bevel: darker towards the edges
    yy, xx = np.mgrid[0:size, 0:size]
    edge = np.minimum(np.minimum(xx, size - 1 - xx), np.minimum(yy, size - 1 - yy)) / (
        0.12 * size
    )
    shade = 0.72 + 0.28 * np.clip(edge, 0, 1)
    tex = (tex * shade[..., None]).astype(np.uint8)
    g = make_cube_glyphs.draw(str(value), font, size=200)
    gh, gw = g.shape
    s = min(0.62 * size / gh, (0.74 if value >= 10 else 0.5) * size / gw)
    g = cv2.resize(
        g, (max(1, int(gw * s)), max(1, int(gh * s))), interpolation=cv2.INTER_AREA
    )
    y0, x0 = (size - g.shape[0]) // 2, (size - g.shape[1]) // 2
    a = (g / 255.0)[..., None]
    roi = tex[y0 : y0 + g.shape[0], x0 : x0 + g.shape[1]].astype(np.float64)
    tex[y0 : y0 + g.shape[0], x0 : x0 + g.shape[1]] = (
        roi * (1 - a) + np.float64(ink_c) * a
    ).astype(np.uint8)
    return tex


def paste(photo, corners, uv, value, font, colours, rng):
    """The photo with a cube of the number pasted flat on the board's plane at uv (of the playing area)."""
    H = cv2.getPerspectiveTransform(
        np.float32([(0, 0), (1, 0), (1, 1), (0, 1)]), np.float32(corners)
    )
    c = np.float64(corners)
    aspect = (np.linalg.norm(c[1] - c[0]) + np.linalg.norm(c[2] - c[3])) / (
        np.linalg.norm(c[3] - c[0]) + np.linalg.norm(c[2] - c[1])
    )
    pw = 1 / (2 + 0.16) / 6  # a point's width, of the playing area's
    side = (
        rng.uniform(0.78, 0.95) * pw * 1.05
    )  # a cube is a little smaller than a checker is wide
    t = rng.uniform(0, 2 * math.pi)
    d = np.array([[math.cos(t), -math.sin(t)], [math.sin(t), math.cos(t)]]) * side / 2
    # the square in board units (u across; v scaled so that a square stays square), then to uv
    sq = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1]]) @ d.T
    sq = sq * [1, aspect] + uv
    img_pts = cv2.perspectiveTransform(np.float32(sq)[None], H)[0]
    tex = face_texture(value, font, colours, rng)
    n = tex.shape[0]
    M = cv2.getPerspectiveTransform(
        np.float32([(0, 0), (n, 0), (n, n), (0, n)]), img_pts
    )
    h, w = photo.shape[:2]
    # a soft shadow a little to one side, then the face
    sh = np.zeros((h, w), np.float32)
    cv2.fillConvexPoly(sh, np.int32(img_pts + (0.08 * side * w, 0.10 * side * w)), 1.0)
    sh = cv2.GaussianBlur(sh, (0, 0), 0.06 * side * w + 1)
    out = (photo * (1 - 0.45 * sh[..., None])).astype(np.uint8)
    warped = cv2.warpPerspective(tex, M, (w, h), flags=cv2.INTER_AREA)
    mask = (
        cv2.warpPerspective(
            np.full((n, n), 255, np.uint8), M, (w, h), flags=cv2.INTER_AREA
        )
        / 255.0
    )
    out = (out * (1 - mask[..., None]) + warped * mask[..., None]).astype(np.uint8)
    # the camera's softness and noise over the cube
    x0, y0 = np.int32(img_pts.min(0) - 40).clip(0)
    x1, y1 = np.int32(img_pts.max(0) + 40)
    roi = out[y0:y1, x0:x1].astype(np.float64)
    roi = cv2.GaussianBlur(roi, (0, 0), rng.uniform(0.6, 1.6)) + rng.normal(
        0, 3, roi.shape
    )
    out[y0:y1, x0:x1] = np.clip(roi, 0, 255).astype(np.uint8)
    return out


def main():
    rng = np.random.default_rng(25)
    values = [2, 4, 8, 16, 32, 64]
    k = 0
    for base, spots in SPOTS.items():
        t = json.load(open(os.path.join(SAMPLES, base + ".truth.json")))
        photo = cv2.imread(os.path.join(SAMPLES, t["image"]))
        # as the app sends it (analyzer/static/app.js UPLOAD_MAX): smaller files, and the size read in use
        f = APP_SIDE / max(photo.shape[:2])
        photo = cv2.resize(
            photo,
            (round(photo.shape[1] * f), round(photo.shape[0] * f)),
            interpolation=cv2.INTER_AREA,
        )
        t["corners_TL_TR_BR_BL"] = [
            [round(x * f, 1), round(y * f, 1)] for x, y in t["corners_TL_TR_BR_BL"]
        ]
        for i, (uv, at) in enumerate(spots):
            value = values[i]
            font = make_cube_glyphs.TEST_FONTS[k % len(make_cube_glyphs.TEST_FONTS)]
            colours = FACES[k % len(FACES)]
            k += 1
            out = paste(
                photo,
                t["corners_TL_TR_BR_BL"],
                np.float64(uv),
                value,
                font,
                colours,
                rng,
            )
            name = f"synth-cube-{base}-{value}"
            cv2.imwrite(
                os.path.join(SAMPLES, name + ".jpg"),
                out,
                [cv2.IMWRITE_JPEG_QUALITY, 88],
            )
            truth = {k2: v for k2, v in t.items() if k2 not in ("note", "dice", "cube")}
            truth.update(
                image=name + ".jpg",
                synthetic=True,
                note=f"{base} with a cube showing {value} pasted in ({at}, font {font}; synth_cube.py, TODO-025)",
                cube={"at": "black" if at == "field" else at, "value": value},
            )
            if (
                at == "field"
            ):  # just doubled by the side on roll (white): black takes or passes
                truth["on_roll"] = "white"
            json.dump(
                truth,
                open(os.path.join(SAMPLES, name + ".truth.json"), "w"),
                ensure_ascii=False,
            )
            print(name, at, uv, font)


if __name__ == "__main__":
    main()
