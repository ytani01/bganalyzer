"""recognizer/corners.py: the far / near side of a screen photo goes inside the rows of numbers (TODO-175)."""

import json
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

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


def test_top_side_stays_near_the_boards_edge_not_the_checkers_tops():
    """Backgammon Galaxy's screen (id hedmzy): the frame of the rows of numbers has the board's edge just
    inside it; the top left corner was 51 px (of 2048) off, on the line along the top checkers
    (after TODO-175: 19 px).
    Skipped until recognizer/import_collected.py has put the photo in samples/ (now only in the Pi's collected/)."""
    img, truth = _sample("hedmzy")
    if img is None:
        pytest.skip("samples/ has no photo with id hedmzy yet")
    found = np.float64(corners.find_corners(img))
    assert np.linalg.norm(found[0] - truth[0]) < 35
