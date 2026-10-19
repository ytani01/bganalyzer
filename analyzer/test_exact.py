"""recognizer/exact.py: arithmetic that comes out the same on every CPU (TODO-046)."""

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "recognizer"))
import exact  # noqa: E402


def _warp_in_numpy(img, M, size):
    """The integer bilinear warp exact.warp promises, written out in numpy."""
    w, h = size
    (a, b, c), (d, e, f), (g, k, m33) = exact.mat(exact.inv3(M))
    u = np.arange(w, dtype=np.float64)[None, :]
    v = np.arange(h, dtype=np.float64)[:, None]
    W = g * u + k * v + m33
    fx = np.floor((a * u + b * v + c) / W * 32 + 0.5).astype(np.int64)
    fy = np.floor((d * u + e * v + f) / W * 32 + 0.5).astype(np.int64)
    x0, y0, ax, ay = fx >> 5, fy >> 5, fx & 31, fy & 31
    acc = np.zeros((h, w, img.shape[2]), np.int64)
    for dy, wy in ((0, 32 - ay), (1, ay)):
        for dx, wx in ((0, 32 - ax), (1, ax)):
            xx, yy = x0 + dx, y0 + dy
            ok = (xx >= 0) & (xx < img.shape[1]) & (yy >= 0) & (yy < img.shape[0])
            acc[ok] += img[yy[ok], xx[ok]].astype(np.int64) * (wx * wy)[ok][:, None]
    return ((acc + 512) >> 10).astype(np.uint8)


def test_warp_is_the_integer_formula():
    rng = np.random.default_rng(0)
    img = rng.integers(0, 256, (90, 120, 3), np.uint8)
    M = np.array([[1.3, 0.1, -10.25], [-0.05, 1.2, 4.5], [1e-3, -5e-4, 1.0]])
    assert (exact.warp(img, M, (150, 110)) == _warp_in_numpy(img, M, (150, 110))).all()


def test_homography_and_fits():
    rng = np.random.default_rng(1)
    H = np.array([[1.1, 0.05, 30], [0.02, 0.9, -20], [1e-4, 2e-5, 1]])
    src = rng.uniform(0, 1000, (12, 2))
    dst = exact.apply_h(H, src)
    assert np.abs(exact.homography(src[:4], dst[:4]) - H).max() < 1e-9
    assert np.abs(exact.homography(src, dst) - H).max() < 1e-9
    # one far outlier is dropped
    bad = np.vstack([dst, [[900, 900]]])
    assert (
        np.abs(exact.homography_robust(np.vstack([src, [[5, 5]]]), bad, 2.0) - H).max()
        < 1e-6
    )
    assert np.abs(exact.mul3(H, exact.inv3(H)) - np.eye(3)).max() < 1e-12
    assert np.allclose(
        exact.polyfit1([1, 2, 3, 5], [2, 4, 7, 9]),
        np.polyfit([1, 2, 3, 5], [2, 4, 7, 9], 1),
    )
    x = np.array([0.5, 2.25, 7.0])
    assert np.allclose(
        exact.interp(x, np.arange(5), [0, 1, 4, 9, 16]),
        np.interp(x, np.arange(5), [0, 1, 4, 9, 16]),
    )


def test_kmeans_in_integers():
    rng = np.random.default_rng(2)
    pts = np.vstack(
        [rng.integers(0, 20, (50, 3)), rng.integers(100, 120, (50, 3))]
    ).astype(np.int32)
    lbl, centres = exact.kmeans(pts, 2)
    assert len(set(lbl[:50])) == 1 and len(set(lbl[50:])) == 1 and lbl[0] != lbl[50]
    assert centres.dtype.kind == "i"
    assert (exact.kmeans(pts, 2)[0] == lbl).all()


@pytest.mark.parametrize("v", [0.1, -2.75, 1e6 / 3])
def test_snap(v):
    assert exact.snap(v, 1 / 64) * 64 == round(v * 64)
