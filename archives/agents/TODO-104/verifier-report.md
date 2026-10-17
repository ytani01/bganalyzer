# TODO-104 確認報告（verifier）

対象: ブランチ claude/todo-104-near-edge、HEAD 7be13f4。`recognizer/corners.py` の `SLOPES` を ±100（傾き 0.5）に広げた変更。

## 1. check_corners.py（5 枚だけ）

実行: `uv run python recognizer/check_corners.py samples/photo5.truth.json samples/photo6.truth.json samples/collected-tad9pt.truth.json samples/collected-bfqwve.truth.json samples/commons-rollup-oblique.truth.json`（終了コード 0）

```
photo5                         4.7%  0.82s
photo6                         3.8%  0.51s
collected-tad9pt               4.5%  0.44s
collected-bfqwve               5.7%  0.60s
commons-rollup-oblique            -  0.12s
within 3.6%: 0, further: 4, not found: 1
```

- photo5 4.7%: 一致
- photo6 3.8%: 一致
- collected-tad9pt 4.5%: 一致
- collected-bfqwve 5.7%: 一致
- commons-rollup-oblique は「-」: 一致

## 2. pytest（通常）

実行: `uv run pytest analyzer/test_api.py -k test_corners_are_found_on_samples -q`（終了コード 0）

```
1 passed, 47 deselected, 1 warning in 5.76s
```

一致（通る）。

## 3. 壊すと落ちるか

`recognizer/corners.py` の `np.arange(-100, 101, 2)` を `np.arange(-60, 61, 2)` に一時的に変えて、手順 2 と同じテストを流した。

```
MUTATED:  recognizer/corners.py | 2 +-
...
>           assert _corner_error(found, t["corners_TL_TR_BR_BL"], img.shape) < most, name
E           AssertionError: photo6
E           assert 0.2328683363759161 < 0.05
...
analyzer/test_api.py:207: AssertionError
FAILED analyzer/test_api.py::test_corners_are_found_on_samples - AssertionErr...
1 failed, 47 deselected, 1 warning in 5.31s
```

- photo6 で落ちた（誤差 0.233、基準 0.05 未満）。狙いどおり: 傾きの上限を戻すと photo6 が外れる。
- 終了コードは記録できなかった（zsh の `PIPESTATUS` が空だった）。出力の「1 failed」から非ゼロと判断した。
- 元に戻したあと `git diff --quiet` で空を確かめた。`git status --short` も空（変更なし）。

## 4. README の 0.23.2 段落と archives の照合

README 298〜301 行目の数値を、`check_corners-0.23.1.txt`・`-0.23.2.txt` と突き合わせた。

| 項目 | README | 0.23.1 | 0.23.2 | 判定 |
|---|---|---|---|---|
| photo5 | 見つからない → 4.7% | - | 4.7% | 一致 |
| photo6 | 23.3% → 3.8% | 23.3% | 3.8% | 一致 |
| collected-tad9pt | 36.7% → 4.5% | 36.7% | 4.5% | 一致 |
| commons-case-midgame | 7.7% → 4.2% | 7.7% | 4.2% | 一致 |
| collected-ajxlol | 見つからない → 9.1% | - | 9.1% | 一致 |
| collected-bfqwve | 4.3% → 5.7% | 4.3% | 5.7% | 一致 |
| commons-rollup-oblique | 28.5% → 見つからない | 28.5% | - | 一致 |
| 3.6% 以内 | 35 のまま | 35 | 35 | 一致 |
| 秒の合計 | 26.4 → 30.7 秒（16% 増） | 26.42 | 30.71 | 一致（増加率 16.2%） |

秒の合計は、各行の時間の列を足して求めた（57 枚。awk で数えた値から、末尾の集計行の 35 を引いた）。

判断できなかったこと:
- 段落の「photo5 の奥の辺 0.36、photo6 の左の辺 0.39」や「正解（点数 0.79）」「1.06〜1.08」などの点数・傾きの値は、archives の出力に無いので照合していない。
- 「24 に増やしても変わらない」「90° 回しても拾えなかった」などの実験の記述も、出力が無いので照合していない。

## 食い違い

なし（確かめられた数値はすべて一致）。

## 確かめられなかったこと

- 「1 failed」の終了コードの数値そのもの（上記のとおり）。
- README の段落の、出力に載っていない数値（上記）。
- コードは直していない。コミットもしていない。
