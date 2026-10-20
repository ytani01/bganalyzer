"""Dice found from their pips when they show as no square (TODO-079: recognizer/dice.py)."""

import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "recognizer"))
import board  # noqa: E402


def test_clear_dice_in_an_oblique_photo_are_read_from_their_pips():
    """photo-black-blue-oblique's small clear green 6-2: seen from the side, each die's sides add to
    its top face and no square is found; the pips still sit like a face."""
    t = json.loads(
        (ROOT / "samples" / "photo-black-blue-oblique.truth.json").read_text()
    )
    img = cv2.imread(str(ROOT / "samples" / t["image"]))
    _, info = board.recognize(img, np.float64(t["corners_TL_TR_BR_BL"]), home=t["home"])
    assert info["dice"]["values"] == [6, 2]
