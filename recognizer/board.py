"""Read a backgammon position from a phone photo of a real board.

Pipeline
  1. Geometry: 4 rough corners of the playing area (both fields + bar, inner
     edge of the frame, as seen by the bottom player) -> homography to a
     canonical top-down board.
  2. Refinement: snap the frame edges to straight lines, then re-fit the
     homography to the printed triangles (tips and sides). The triangles lie
     on the board surface, so unlike the raised frame they are not shifted
     in oblique photos.
  3. Colours: plain field and the two triangle colours are sampled inside
     detected triangles; frame colours just outside the field.
  4. Checkers: circles of the known radius found by radial symmetry (radial.py;
     Hough before 0.20.0), kept when the circle has strong radial edges,
     a solid interior and a colour unlike what an empty spot there would
     show; dropped where the triangle's sides show through. Where the sides
     are hidden from the frame on and at most one circle was found, a stack
     is added (dark checkers on a dark board make no circle). The two checker
     colours are split by 2-means.
  5. Counting: circles are assigned to the nearest point column; the
     farthest checker from the point base gives the stack height (so a
     checker missed in the middle of a stack is still counted).
     Borne-off = 15 - (on board + bar).

Canonical frame (ground plane, pixels): x 0..W left->right, y 0..H top->bottom.
"Bottom" is the side of the player whose perspective `corners` uses.

This file runs the pipeline (recognize) and maps the counts to a Position. The steps live in
geometry.py (1-2), colours.py (3), checkers.py (4-5) and overlay.py (what the app draws over the
photo); dice.py and cube.py read the dice and the cube, tracing.py records each step's value.
"""
from __future__ import annotations

import json

import cv2
import numpy as np

import cube as cube_reader
import dice as dice_reader
import exact
import home_prior
from checkers import add_hidden_stacks, count_from_circles, detect_checkers, lab_gradients
from colours import board_colours, triangle_colour_map
from geometry import (H_CAN, OBLIQUE_WARN_DEG, TRI_DEPTH, Layout, camera_from_h, find_tips, fit_columns,
                      fit_columns_to_checkers, refine, refine_tips, snap_layout, to_ground, view_tilt_deg)
from overlay import geometry_checkers, geometry_counts, geometry_frame, geometry_square, geometry_tips, save_debug
from position import Position
from tracing import trace as _trace

# The recognizer's version (the reading code in recognizer/: board.py and the modules it uses, corners.py). Bump it when recognizer/ changes;
# the analyzer has its own in analyzer/app.py. How to bump: CLAUDE.md.
__version__ = "0.21.2"


def to_position(runs, bar, bottom_colour: int, home: str) -> Position:
    """Map canonical columns to White's point numbers.

    White = bottom player (colour index `bottom_colour`), home board on
    `home` side ('left' or 'right') of the bottom row.
    """
    p = Position()
    for (c, row), (col, n) in runs.items():
        if n == 0 or col is None:
            continue
        cc = c if home == "right" else 11 - c  # mirror so home is on the right
        # bottom row right->left = 1..12, top row left->right = 13..24
        pt = (12 - cc) if row == "bottom" else (13 + cc)
        p.points[pt - 1] = n if col == bottom_colour else -n
    p.bar_white = bar[bottom_colour]
    p.bar_black = bar[1 - bottom_colour]
    w = sum(n for n in p.points if n > 0) + p.bar_white
    b = -sum(n for n in p.points if n < 0) + p.bar_black
    p.off_white, p.off_black = max(15 - w, 0), max(15 - b, 0)
    return p


def recognize(img, corners, *, bottom_colour=0, home="right", bar_ratio=None,
              a_ratio=None, debug_prefix=None, method="circles", trace=None, progress=None):
    """corners: TL, TR, BR, BL of the playing area as seen from the bottom player.
    home: 'left', 'right' or 'auto' (guessed from the checkers; info['home'] says which).
    trace: a list to append (step, hash of its value) to, for finding where two machines part.
    progress: called as progress(stage, data) when each stage is done ("fit" four times: the frame
    fitted to the frame's edges twice, then to the triangles twice; then "tips", "checkers", "counts",
    "dice", "cube"), with the parts of info["geometry"] it found (image pixels), for showing the
    reading as it goes. It does not change what is read."""
    finder = {"hough": "hough", "radial+hough": "both"}.get(method, "radial")
    emit = progress or (lambda stage, data: None)
    cv2.setRNGSeed(0)  # k-means initialisation: make runs repeatable
    _trace(trace, "image", img)
    m = 60
    corners = exact.snap(np.float64(corners).reshape(4, 2), 1 / 64)
    H0 = exact.homography(np.float64([(0, 0), (1, 0), (1, 1), (0, 1)]), corners)
    K, *_ = camera_from_h(H0, img.shape)
    B = exact.mul3(exact.inv3(K), H0)
    aspect = a_ratio or exact.snap(np.clip(exact.norm(B[:, 0]) / exact.norm(B[:, 1]), 0.9, 1.4), 1e-6)
    br = bar_ratio or 0.16
    a = aspect * H_CAN / (2 + br)
    lay = snap_layout(Layout(a=a, bar=a * br))
    _trace(trace, "start", [H0, K, aspect, a])
    # 1. geometry: frame edges, then the printed triangles
    H, quality, lay = refine(img, corners, lay, m)
    _trace(trace, "refine1", [H, quality, lay.a, lay.bar])
    emit("fit", geometry_frame(H, lay) | dict(by="edges", round=1))
    H, quality, lay = refine(img, exact.apply_h(H, lay.src_pts()), lay, m)
    _trace(trace, "refine2", [H, quality, lay.a, lay.bar])
    emit("fit", geometry_frame(H, lay) | dict(by="edges", round=2))
    tips = []
    reach = 1.2
    for round_ in range(2):
        size = (int(lay.w + 2 * m), int(lay.h + 2 * m))
        ground = to_ground(img, H, m, size)
        _trace(trace, "ground_loop", ground)
        lay = fit_columns(ground, lay, m, reach)
        _trace(trace, "fit_columns", [lay.a, lay.bar, lay.cols])
        H, lay, tips = refine_tips(img, H, lay, m)
        _trace(trace, "refine_tips", [H, lay.a, lay.bar, lay.cols, tips])
        emit("fit", geometry_frame(H, lay) | dict(by="triangles", round=round_ + 1))
        if lay.cols is None:
            # fitted to the triangles: from here on only small corrections, as other
            # things on the board can look like triangles too
            reach = 0.4
    size = (int(lay.w + 2 * m), int(lay.h + 2 * m))
    ground = to_ground(img, H, m, size)
    _trace(trace, "ground", ground)
    tips = find_tips(ground, lay, m)
    _trace(trace, "tips", tips)
    emit("tips", dict(tips=geometry_tips(tips, H)))
    board = board_colours(ground, lay, m, tips)
    _trace(trace, "board_colours", board)
    pitch = lay.pw * 1.05
    # 2. counting
    ground_lab = cv2.cvtColor(ground, cv2.COLOR_BGR2Lab).astype(np.float32)
    tri_map = triangle_colour_map(board, lay, m, tips, ground_lab)
    tri_len = np.median([t[4] for t in tips]) if tips else TRI_DEPTH * lay.h
    # measured with all the circles: which ones show the triangle's sides must not change the size
    _trace(trace, "tri_map", [tri_map, tri_len])
    circles = detect_checkers(ground, board, lay, m, pitch, tri_map, tri_len, drop_shown=False, finder=finder)
    _trace(trace, "circles1", circles)
    if len(circles) >= 4:   # checkers may be wider than a point: measure them
        pitch = float(2 * np.median([c[2] for c in circles]))
        circles = detect_checkers(ground, board, lay, m, pitch, tri_map, tri_len, finder=finder)
    _trace(trace, "circles2", [pitch, circles])
    if len(circles) >= 4:   # learn the board colours again without the checkers on it
        mask = np.zeros(ground.shape[:2], np.uint8)
        for x, y, r, *_ in circles:
            cv2.circle(mask, (int(x + m), int(y + m)), int(r * 1.1), 1, -1)
        board = board_colours(ground, lay, m, tips, mask.astype(bool))
        tri_map = triangle_colour_map(board, lay, m, tips, ground_lab)
        circles = detect_checkers(ground, board, lay, m, pitch, tri_map, tri_len, finder=finder)
    _trace(trace, "circles3", [board, circles])
    lay2 = fit_columns_to_checkers(lay, circles)
    if lay2.cols != lay.cols:
        lay = lay2
        tri_map = triangle_colour_map(board, lay, m, tips, ground_lab)
        circles = detect_checkers(ground, board, lay, m, pitch, tri_map, tri_len, finder=finder)
    # last, so that the added checkers do not change the measured pitch or the board colours
    circles = add_hidden_stacks(ground, lay, m, pitch, circles)
    _trace(trace, "circles4", [lay.cols, circles])
    runs, bar, cc = count_from_circles(circles, lay, pitch)
    _trace(trace, "count", [sorted(runs.items()), bar, cc])
    if method == "slots" and cc is not None:   # experimental (TODO-032): slots.py
        import slots
        labf = cv2.GaussianBlur(ground_lab, (0, 0), 1.5)
        gx = sum(cv2.Sobel(labf[:, :, i], cv2.CV_32F, 1, 0) for i in range(3))
        gy = sum(cv2.Sobel(labf[:, :, i], cv2.CV_32F, 0, 1) for i in range(3))
        runs = slots.count_by_slots(ground_lab, gx, gy, board, lay, m, pitch, tri_map, tri_len,
                                    cc, circles, runs)
    if method == "section" and cc is not None:   # experimental (TODO-032 idea 2): section.py
        import section
        _, _, gy8 = lab_gradients(ground)
        runs = section.count_by_profile(ground_lab, gy8, board, lay, m, pitch, tri_map, tri_len,
                                        cc, circles, runs)
    guessed = None
    if home == "auto":   # which way the checkers move: guess from where they stand
        home, margin = home_prior.guess(to_position(runs, bar, bottom_colour, "right").points)
        guessed = dict(margin=round(float(margin), 1))
    pos = to_position(runs, bar, bottom_colour, home)
    checkers = geometry_checkers(circles, cc, bottom_colour, H)
    counts = geometry_counts(runs, bar, bottom_colour, lay, H)
    emit("checkers", geometry_frame(H, lay) | dict(checkers=checkers))
    emit("counts", dict(counts=counts, home=home, home_guess=guessed))
    info = dict(home=home, home_guess=guessed, edge_quality=float(quality), tips=len(tips), circles=len(circles),
                layout=dict(a=float(lay.a), bar=float(lay.bar), h=float(lay.h)), pitch=float(pitch),
                checker_lab=None if cc is None else cc.round(1).tolist(),
                board_lab=board.round(1).tolist())
    # Where the playing area and its columns ended up, for showing the photo next to the read board:
    # corners in image pixels (TL TR BR BL), columns and bar edges as fractions of the width.
    info["geometry"] = geometry_frame(H, lay) | dict(tips=geometry_tips(tips, H), checkers=checkers, counts=counts)
    info["dice"] = dice_reader.read_dice(img, H, lay, pitch, circles,
                                         debug=debug_prefix and debug_prefix + "_dice.jpg", trace=trace)
    _trace(trace, "dice", info["dice"])
    # the dice and the cube found, for the reading overlay too (the dice read with confidence in the
    # fields: the ones dice_read can come from)
    info["geometry"]["dice"] = [dict(quad=geometry_square(d, H), value=d["value"])
                                for d in info["dice"]["dice"] if d["sure"] and not d["on_bar"]]
    emit("dice", dict(dice=info["geometry"]["dice"]))
    info["cube"] = cube_reader.read_cube(img, H, lay, pitch, circles, info["dice"]["dice"],
                                         debug=debug_prefix and debug_prefix + "_cube.jpg")
    _trace(trace, "cube", info["cube"])
    cube = info["cube"]
    info["geometry"]["cube"] = cube and dict(quad=geometry_square(cube, H), at=cube["at"], value=cube.get("value"))
    emit("cube", dict(cube=info["geometry"]["cube"]))
    info["tilt_deg"] = round(view_tilt_deg(corners, img.shape), 1)
    info["warnings"] = ["oblique"] if info["tilt_deg"] > OBLIQUE_WARN_DEG else []
    if debug_prefix:
        save_debug(debug_prefix, ground, lay, m, runs, tips, circles)
    return pos, info


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--corners", required=True, help="x1,y1,x2,y2,x3,y3,x4,y4 (TL,TR,BR,BL)")
    ap.add_argument("--home", default="right", choices=["left", "right", "auto"])
    ap.add_argument("--bottom-colour", type=int, default=0)
    ap.add_argument("--debug")
    args = ap.parse_args()
    img = cv2.imread(args.image)
    c = list(map(float, args.corners.split(",")))
    pos, info = recognize(img, list(zip(c[0::2], c[1::2])), home=args.home,
                          bottom_colour=args.bottom_colour, debug_prefix=args.debug)
    print(pos.ascii())
    print(json.dumps({**pos.to_dict(), "info": info}, ensure_ascii=False))
