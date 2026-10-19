"""recognizer/corners.py: the far / near side of a screen photo goes inside the rows of numbers (TODO-175)."""

import json
import os
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "recognizer"))
import corners  # noqa: E402

COLLECTED = Path(os.environ.get("BG_COLLECTED", ROOT / "collected"))


def test_top_side_of_a_screen_photo_is_not_the_checkers_tops():
    """Backgammon Galaxy's screen, as taken (collected/user-*-hedmzy; the Pi's, not in the repository):
    the top left corner was 51 px (of 2048) off, on the line along the top checkers; with the fix 19 px.
    Not on samples/collected-galaxy-screen-9, the same photo painted black outside the board: there main finds
    the same corners as the fix (42 px), the frame of the rows of numbers being painted over."""
    names = sorted(COLLECTED.glob("user-*-hedmzy.truth.json"))
    if not names:
        pytest.skip("collected/ has no photo hedmzy")
    t = json.loads(names[0].read_text())
    img = cv2.imread(str(COLLECTED / t["image"]))
    found = np.float64(corners.find_corners(img))
    assert np.linalg.norm(found[0] - np.float64(t["corners_TL_TR_BR_BL"][0])) < 35
