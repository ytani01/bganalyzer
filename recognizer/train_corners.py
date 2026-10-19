"""Train the model that finds roughly where the board is (TODO-136), and write it as ONNX.

YOLO-pose with one class (board): box = the corners' bounding box, 4 keypoints = TL, TR, BR, BL
of the playing area as in samples/*.truth.json. All the real photos are used (synth-cube-*, made
from photo-blue-red-top / photo-carved-brown-top, and samples/external are left out), each with copies under a random
perspective; many collected-* have the outside of the board filled with black, so in the copies
that black is replaced by a random background. synth.py's boards are added, and the photos of any
COCO exports given (a polygon round the playing area each, as Roboflow's; TODO-136). corners.py runs the
model with OpenCV's dnn (corners_model.onnx), so the app needs neither torch nor ultralytics.

usage (from the repository's top; about 50 minutes on 16 CPU cores):
  uv run --no-project --python 3.12 --index https://download.pytorch.org/whl/cpu \\
    --index-strategy unsafe-best-match --with torch --with torchvision --with ultralytics --with onnx --with onnxslim \\
    python recognizer/train_corners.py <work_dir> [epochs] [coco_dir ...]
writes recognizer/corners_model.onnx (the dataset and the run are left in work_dir).
"""

import glob
import json
import os
import shutil
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import synth  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
LONG = 1024
COPIES = 4
N_SYNTH = 60
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
    bg = np.broadcast_to(
        ramp[None] if len(ramp) == w else ramp[:, None], (h, w, 3)
    ).copy()
    for _ in range(rng.integers(0, 6)):
        x, y = rng.integers(0, w), rng.integers(0, h)
        cv2.rectangle(
            bg,
            (x, y),
            (x + rng.integers(20, w // 2), y + rng.integers(20, h // 2)),
            rng.integers(0, 256, 3).tolist(),
            -1,
        )
    bg = cv2.GaussianBlur(bg, (0, 0), rng.uniform(1, 8))
    return np.clip(bg + rng.normal(0, rng.uniform(2, 12), bg.shape), 0, 255).astype(
        np.uint8
    )


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
    out = cv2.warpPerspective(
        img, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0)
    )
    return out, cv2.perspectiveTransform(pts[None].astype(np.float32), M)[0]


def label(pts, w, h):
    x0, y0 = pts.min(0)
    x1, y1 = pts.max(0)
    box = [(x0 + x1) / 2 / w, (y0 + y1) / 2 / h, (x1 - x0) / w, (y1 - y0) / h]
    kp = [v for x, y in pts for v in (x / w, y / h, 2)]
    return "0 " + " ".join(f"{v:.6f}" for v in box + kp) + "\n"


def write(out, split, name, img, pts):
    if not (
        (pts >= 0).all()
        and (pts[:, 0] < img.shape[1]).all()
        and (pts[:, 1] < img.shape[0]).all()
    ):
        return
    cv2.imwrite(f"{out}/images/{split}/{name}.jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 90])
    open(f"{out}/labels/{split}/{name}.txt", "w").write(
        label(pts, img.shape[1], img.shape[0])
    )


def order(pts):
    """TL, TR, BR, BL of four points, as they lie in the image."""
    s, d = pts.sum(1), pts[:, 1] - pts[:, 0]
    return pts[[s.argmin(), d.argmin(), s.argmax(), d.argmax()]]


def add_coco(out, root):
    """The photos of a COCO export (train / valid / test), each with its polygon's four corners."""
    for f in sorted(glob.glob(f"{root}/*/_annotations.coco.json")):
        d = json.load(open(f))
        names = {i["id"]: i["file_name"] for i in d["images"]}
        for a in d["annotations"]:
            if not a.get("segmentation"):
                continue
            hull = cv2.convexHull(np.float32(a["segmentation"][0]).reshape(-1, 2))
            q = cv2.approxPolyDP(hull, 0.02 * cv2.arcLength(hull, True), True).reshape(
                -1, 2
            )
            q = order(np.float32(q)) if len(q) == 4 else None
            if (
                q is None or len(np.unique(q, axis=0)) < 4
            ):  # not four corners, or a diamond order() cannot tell apart
                continue
            img, pts = shrink(
                cv2.imread(os.path.join(os.path.dirname(f), names[a["image_id"]])), q
            )
            write(
                out, "train", f"coco-{len(os.listdir(f'{out}/images/train'))}", img, pts
            )


def prepare(out, coco=()):
    for s in ("train", "val"):
        os.makedirs(f"{out}/images/{s}", exist_ok=True)
        os.makedirs(f"{out}/labels/{s}", exist_ok=True)
    samples = os.path.join(HERE, "..", "samples")
    real = [
        f
        for f in sorted(glob.glob(f"{samples}/*.truth.json"))
        if not os.path.basename(f).startswith("synth-cube")
    ]
    val = set(
        rng.choice(real, 5, replace=False)
    )  # also in train: only for ultralytics' own monitoring
    for f in real:
        t = json.load(open(f))
        name = os.path.basename(f).replace(".truth.json", "")
        img, pts = shrink(
            cv2.imread(os.path.join(samples, t["image"])),
            np.float32(t["corners_TL_TR_BR_BL"]),
        )
        write(out, "train", name, img, pts)
        if f in val:
            write(out, "val", name, img, pts)
        for k in range(COPIES):
            a, p = warp(img, pts)
            write(out, "train", f"{name}-aug{k}", replace_black(a), p)
    for k in range(N_SYNTH):
        board, corners = synth.render_board(
            synth.random_position(rng), rng, home="right" if k % 2 else "left"
        )
        photo, c = synth.photograph(board, corners, rng, tilt=0.08)
        img, pts = shrink(photo, c)
        write(out, "train", f"synth-{k:03d}", img, pts)
    for root in coco:
        add_coco(out, root)
    open(f"{out}/data.yaml", "w").write(
        f"path: {os.path.abspath(out)}\ntrain: images/train\nval: images/val\n"
        "kpt_shape: [4, 3]\nflip_idx: [1, 0, 3, 2]\nnames:\n  0: board\n"
    )


def main(work, epochs, coco=()):
    from ultralytics import YOLO

    prepare(f"{work}/data", coco)
    YOLO("yolo11n-pose.pt").train(
        data=f"{work}/data/data.yaml",
        project=f"{work}/runs",
        name="corners",
        exist_ok=True,
        epochs=epochs,
        imgsz=640,
        batch=16,
        device="cpu",
        workers=8,
        mosaic=0.0,
        degrees=10,
        scale=0.4,
        translate=0.1,
        fliplr=0.5,
        plots=False,
    )
    onnx = YOLO(f"{work}/runs/corners/weights/best.pt").export(
        format="onnx", imgsz=640, opset=12, simplify=True
    )
    shutil.copyfile(onnx, os.path.join(HERE, "corners_model.onnx"))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 60, sys.argv[3:])
