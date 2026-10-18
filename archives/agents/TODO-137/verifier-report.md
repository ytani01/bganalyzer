# TODO-137 確認の報告（verifier）

確認の対象: bganalyzer（ブランチ claude/todo-137-side-quarter、未コミットの差分）。コードは変更していない（手順 2 の一時変更は戻し済み）。

## 1. analyzer/test_side.py が通るか — 合った

- 実行: `uv run pytest -q analyzer/test_side.py`
- 終了コード: 0
- 最後の行: `17 passed, 1 warning in 24.07s`

## 2. 直しを効かなくすると、photo4 のテストが落ちるか — 合った

- 一時変更: `recognizer/side.py` の `PART = 0.6` を `PART = 2` に変更（`sed` で行頭の 1 行だけ）
- 実行: `uv run pytest -q analyzer/test_side.py -k photo4`
- 終了コード: 1（落ちた）
- 落ちた箇所（出力のまま）:
  ```
  FAILED analyzer/test_side.py::test_api_find_corners_keeps_photo4_from_the_front
  analyzer/test_side.py:125: AssertionError
  E       AssertionError: assert 'left' is None
  1 failed, 16 deselected, 1 warning in 6.48s
  ```
- 戻し: 変更前に保存したコピーから `recognizer/side.py` を戻した。sha256 は一致（`3cfc51a09cdcfb01e1263b3b699449dc7b38558bbfacd73851497da5bce42a98`）。`PART = 0.6` の行を確認した。

## 3. 判定の変化（TODO-105 の side-new.json との比較）— 合った

- 実行: `uv run python archives/agents/TODO-105/side_choice.py recognizer <scratchpad>/verifier-side.json`（終了コード 0）
- 出力: `/tmp/claude-649/-home-ytani-work-bganalyzer/9bb735ef-c030-4910-a772-07fef3f64259/scratchpad/verifier-side.json`（ログは同じ scratchpad の `side_choice.log`）
- 件数は両方 67 件、キーも同じ。変わったのは 8 件だけ（点数と way の両方を比べた）。

| サンプル | 直す前 | 直した後 |
|---|---|---|
| collected-w8eaks | left 0.684 | null 0.671 |
| photo4 | left 0.991 | null 0.579 |
| synth-cube-photo4-2 | right 0.976 | null 0.570 |
| synth-cube-photo4-4 | left 0.954 | null 0.518 |
| synth-cube-photo4-8 | right 0.949 | null 0.577 |
| synth-cube-photo4-16 | right 0.976 | null 0.565 |
| synth-cube-photo4-32 | right 0.939 | null 0.553 |
| synth-cube-photo4-64 | right 0.864 | null 0.584 |

- TODO.md の記述と一致: 変わったのは指定の 8 枚だけで、全部 way が null になった。残りの 59 枚は way と点数が同じ。
- 直した後に way が null でないのは 5 枚で、TODO.md の記述と一致: collected-4b88u3（right）、collected-gka56t（left）、collected-ydz20m（right）、commons-rollup-oblique（left）、screen2（right）。

## 確かめられなかったこと・判断が要ること

- 境界線上の判断は報告だけ（実害は未確認）。
  - screen2 は直した後も right（0.53 で ri4m9g の 0.50 と近い）。TODO.md に「分けられない」とある。
  - PART = 0.6 の良し悪しは判断していない。
- 手順 2 は PART を 2 にして確かめた。0.6 から別の値に動かした場合の挙動は確かめていない。
- テスト全体は流していない（指示どおり）。精度の測り直しもしていない。
