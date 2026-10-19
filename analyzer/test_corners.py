"""recognizer/corners.py: the far / near side of a screen photo goes inside the rows of numbers (TODO-175)."""

import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "recognizer"))
import corners  # noqa: E402


def _sample(photo_id):
    for p in sorted((ROOT / "samples").glob("*.truth.json")):
        t = json.loads(p.read_text())
        if t.get("id") == photo_id:
            return cv2.imread(str(p.parent / t["image"])), np.float64(
                t["corners_TL_TR_BR_BL"]
            )
    return None, None


def test_top_side_of_a_screen_photo_stays_near_the_boards_edge():
    """Backgammon Galaxy's screen (samples id hedmzy, collected-galaxy-screen-9).
    Not a test of the TODO-175 fix: the samples/ photo is painted black outside the board, and on it main
    (recognizer 0.29.2) and 0.30.0 find the same corners (top left 42 px off, of 2048); on the photo as taken
    the fix moved that from 51 to 19 px. It only keeps the corners from going far off the board's edge."""
    img, truth = _sample("hedmzy")
    assert img is not None
    found = np.float64(corners.find_corners(img))
    assert np.linalg.norm(found[0] - truth[0]) < 55
