"""TODO-134 確認: POST /find-corners を side 無しで送り、横から撮った写真と正面の写真で side が分かれるかを見る。

実行: cd /home/ytani/work/bganalyzer && uv run python archives/agents/TODO-134/verify.py
"""
import sys
import time
from pathlib import Path

import cv2
import numpy as np
from fastapi.testclient import TestClient

ROOT = Path("/home/ytani/work/bganalyzer")
sys.path.insert(0, str(ROOT / "analyzer"))

from app import app  # noqa: E402


def shrink_long_side(img: np.ndarray, long_side: int = 2048) -> np.ndarray:
    h, w = img.shape[:2]
    scale = long_side / max(h, w)
    if scale >= 1:
        return img
    return cv2.resize(img, (round(w * scale), round(h * scale)), interpolation=cv2.INTER_AREA)


def to_jpeg_bytes(img: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 95])
    assert ok
    return buf.tobytes()


def post(client: TestClient, data: bytes, label: str) -> None:
    t0 = time.perf_counter()
    r = client.post("/find-corners", files={"image": ("photo.jpg", data, "image/jpeg")})
    sec = time.perf_counter() - t0
    print(f"[{label}] status={r.status_code} seconds={sec:.2f}")
    if r.status_code != 200:
        print(f"  body={r.text[:500]}")
        return
    j = r.json()
    corners = j.get("corners")
    n = len(corners) if corners else 0
    print(f"  side={j.get('side')!r} corners_count={n} corners={corners}")
    print(f"  keys={sorted(j.keys())} width={j.get('width')} height={j.get('height')}")


def main() -> None:
    photo5 = cv2.imread(str(ROOT / "samples" / "photo5.jpg"))
    photo2 = cv2.imread(str(ROOT / "samples" / "photo2.jpg"))
    assert photo5 is not None and photo2 is not None

    side_img = shrink_long_side(cv2.rotate(photo5, cv2.ROTATE_90_CLOCKWISE))
    front_img = shrink_long_side(photo2)
    print(f"side_img shape={side_img.shape} front_img shape={front_img.shape}")

    client = TestClient(app)
    post(client, to_jpeg_bytes(side_img), "横から photo5 rotated")
    post(client, to_jpeg_bytes(front_img), "正面 photo2")


if __name__ == "__main__":
    main()
