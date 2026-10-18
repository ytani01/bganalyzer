"""Make a YOLO-pose dataset of the board's four corners (TODO-135).

One class (board), box = the corners' bounding box, 4 keypoints = TL, TR, BR, BL
of the playing area as in samples/*.truth.json. Held-out samples, the
synth-cube-* (made from photo2 / photo4) and samples/external are left out.

Many collected-* photos have the outside of the board filled with black, so
each real photo also gets copies with that black replaced by a random
background, under a random perspective.

usage: python prep.py <out_dir> [n_synth]   (run from the repository's top)
"""
import glob
import json
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, "recognizer")
import synth  # noqa: E402

HELD_OUT = {"photo4", "photo6", "collected-er0y2w"}
LONG = 1024
COPIES = 4
rng = np.random.default_rng(0)


def shrink(img, pts):
    s = LONG / max(img.shape[:2])
    if s < 1:
        img = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        pts = pts * s
    return img, pts


def background(h, w):
    """Random gradient, blotches and noise."""
    c0, c1 = rng.integers(0, 256, 3), rng.integers(0, 256, 3)
    t = np.linspace(0, 1, w if rng.random() < 0.5 else h)[:, None]
    ramp = (c0 + (c1 - c0) * t).astype(np.uint8)
    bg = np.broadcast_to(ramp[None] if len(ramp) == w else ramp[:, None], (h, w, 3)).copy()
    for _ in range(rng.integers(0, 6)):
        x, y = rng.integers(0, w), rng.integers(0, h)
        cv2.rectangle(bg, (x, y), (x + rng.integers(20, w // 2), y + rng.integers(20, h // 2)),
                      rng.integers(0, 256, 3).tolist(), -1)
    bg = cv2.GaussianBlur(bg, (0, 0), rng.uniform(1, 8))
    return np.clip(bg + rng.normal(0, rng.uniform(2, 12), bg.shape), 0, 255).astype(np.uint8)


def replace_black(img):
    """Near-black pixels joined to the image's border -> a random background."""
    dark = (img.max(2) < 12).astype(np.uint8)
    n, lab = cv2.connectedComponents(dark)
    border = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}
    mask = np.isin(lab, list(border)) & (dark > 0)
    if mask.mean() < 0.02:
        return img
    out = img.copy()
    out[mask] = background(*img.shape[:2])[mask]
    return out


def warp(img, pts):
    h, w = img.shape[:2]
    src = np.float32([(0, 0), (w, 0), (w, h), (0, h)])
    dst = (src + rng.uniform(-0.12, 0.12, (4, 2)) * (w, h)).astype(np.float32)
    M = cv2.getPerspectiveTransform(src, dst)
    out = cv2.warpPerspective(img, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
    return out, cv2.perspectiveTransform(pts[None].astype(np.float32), M)[0]


def label(pts, w, h):
    x0, y0 = pts.min(0)
    x1, y1 = pts.max(0)
    box = [(x0 + x1) / 2 / w, (y0 + y1) / 2 / h, (x1 - x0) / w, (y1 - y0) / h]
    kp = [v for x, y in pts for v in (x / w, y / h, 2)]
    return "0 " + " ".join(f"{v:.6f}" for v in box + kp) + "\n"


def write(out, split, name, img, pts):
    if not ((pts >= 0).all() and (pts[:, 0] < img.shape[1]).all() and (pts[:, 1] < img.shape[0]).all()):
        return
    cv2.imwrite(f"{out}/images/{split}/{name}.jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 90])
    open(f"{out}/labels/{split}/{name}.txt", "w").write(label(pts, img.shape[1], img.shape[0]))


def main(out, n_synth):
    for s in ("train", "val"):
        os.makedirs(f"{out}/images/{s}", exist_ok=True)
        os.makedirs(f"{out}/labels/{s}", exist_ok=True)
    files = [f for f in sorted(glob.glob("samples/*.truth.json")) if not os.path.basename(f).startswith("synth-cube")]
    real = [f for f in files if os.path.basename(f).replace(".truth.json", "") not in HELD_OUT]
    val = set(rng.choice(real, 5, replace=False))   # only for ultralytics' own monitoring
    for f in real:
        t = json.load(open(f))
        name = os.path.basename(f).replace(".truth.json", "")
        img, pts = shrink(cv2.imread(os.path.join("samples", t["image"])), np.float32(t["corners_TL_TR_BR_BL"]))
        split = "val" if f in val else "train"
        write(out, split, name, img, pts)
        if split == "val":
            continue
        for k in range(COPIES):
            a, p = warp(img, pts)
            write(out, split, f"{name}-aug{k}", replace_black(a), p)
    for k in range(n_synth):
        pos = synth.random_position(rng)
        board, corners = synth.render_board(pos, rng, home="right" if k % 2 else "left")
        photo, c = synth.photograph(board, corners, rng, tilt=0.08)
        img, pts = shrink(photo, c)
        write(out, "train", f"synth-{k:03d}", img, pts)
    open(f"{out}/data.yaml", "w").write(
        f"path: {os.path.abspath(out)}\ntrain: images/train\nval: images/val\n"
        "kpt_shape: [4, 3]\nflip_idx: [1, 0, 3, 2]\nnames:\n  0: board\n")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 60)
