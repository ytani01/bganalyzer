"""recognizer/tune.py: trying the recognizer's thresholds (TODO-030)."""
import sys
from pathlib import Path

RECOGNIZER = Path(__file__).resolve().parent.parent / "recognizer"
sys.path.insert(0, str(RECOGNIZER))

import tune  # noqa: E402


def test_every_parameter_exists_and_can_be_changed():
    for p in tune.PARAMS:
        module, name = p.split(".")
        assert isinstance(tune.current(p), (int, float)), p
        assert name not in tune.default_args(module), p   # else changing it would not reach the code


def test_compare_counts_gains_and_losses():
    base = {"a": {"points": 20, "bar": True, "home": True, "dice": "ok", "cube": "ok"},
            "b": {"points": 22, "bar": True, "home": True, "dice": "not read", "cube": "ok", "cube_value": "not read"}}
    now = {"a": {"points": 21, "bar": True, "home": True, "dice": "ok", "cube": "ok"},
           "b": {"points": 22, "bar": False, "home": True, "dice": "ok", "cube": "ok", "cube_value": "ok"}}
    gain, better, worse = tune.compare(base, now)
    assert gain == 1
    assert better == ["a points 20 → 21", "b dice not read → ok", "b cube_value not read → ok"]
    assert worse == ["b bar True → False"]


def test_a_small_run_writes_a_report(tmp_path):
    out = tmp_path / "tune.md"
    report = tune.main(["--only", "screen-app-grey-shot", "--params", "cube_value.GAP_MIN", "--steps", "1.2", "--jobs", "1", "--out", str(out)])
    assert out.read_text() == report
    assert "今の設定: **24/24** ポイント" in report
    assert "| cube_value.GAP_MIN | 0.1 | 0.12 | +0 | 0 | 0 |" in report
    assert "何も悪くならない設定は無かった" in report
