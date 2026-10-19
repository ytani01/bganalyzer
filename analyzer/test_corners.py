"""recognizer/corners.py: the far / near side of a screen photo goes inside the rows of numbers (TODO-175)."""

import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "recognizer"))
import corners  # noqa: E402


def test_top_side_of_a_screen_photo_is_not_the_checkers_tops():
    """samples/collected-galaxy-screen-9 (Backgammon Galaxy's screen): the top left corner was 51 px (of 2048)
    off, on the line along the top checkers; with the fix 19 px."""
    t = json.loads(
        (ROOT / "samples" / "collected-galaxy-screen-9.truth.json").read_text()
    )
    img = cv2.imread(str(ROOT / "samples" / t["image"]))
    found = np.float64(corners.find_corners(img))
    assert np.linalg.norm(found[0] - np.float64(t["corners_TL_TR_BR_BL"][0])) < 35
