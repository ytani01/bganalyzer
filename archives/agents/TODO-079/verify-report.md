# TODO-079 確認の報告

確認者: verifier。コードは直していない。コミットしていない。

## 項目ごとの結果

1. photo-black-blue-oblique（1 枚だけ）: 合っている。
   `23/24 points correct, bar ok, home guess ok (+14.7), dice ok (read [6, 2], truth [6, 2]), cube ok (read None, truth centre)`、終了コード 0。
   ポイント 19 は truth -5 / got -4（これは今回の項目の対象外）。
2. commons-lg-cube-dice（1 枚だけ）: 合っている。
   `22/24 points correct, bar ok, home guess ok (+17.1), dice ok (read None, truth None), cube ok (read None, truth centre)`、終了コード 0。
   ポイント 13 と 24 の誤りは今回の項目の対象外。
3. `uv run pytest analyzer/test_dice.py`: 合っている。`1 passed in 8.74s`。
4. 壊すと落ちるか: 合っている。
   `recognizer/dice.py` の `read_dice` で、`found, (dice, values, out) = pip_found, more` を `pass` に一時的に変えると、
   `FAILED analyzer/test_dice.py::test_clear_dice_in_an_oblique_photo_are_read_from_their_pips`
   `assert None == [6, 2]`（`analyzer/test_dice.py:23`）。
   その後 `git checkout -- recognizer/dice.py` で戻し、`git status --short` で dice.py の差分が無いことを確認した（diff 0 行）。
   注: 1 回目に流したときの `EXIT=` は `tail` の終了コードだったので、pytest の終了コードは出力の `1 failed` で判断した。
5. 値の一致:
   - `recognizer/board.py` の `__version__ = "0.30.0"`: 合っている。
   - `recognizer/README.md` 371 行「切る位置 60〜195 の 10 段」: 合っている。`dice.py` の `_pip_found` は `range(2 * PIP_CONTRAST, 200, PIP_CONTRAST // 2)` で、`PIP_CONTRAST = 30` のため 60〜195 の 10 段（実測）。

## 手順で起きたこと
- `evaluate.py --help` は `--help` を見ず、全サンプルの測定を始めた（`--help` は無視され、位置引数が無いと全件を読む）。
  約 3 分で止め、プロセスは残っていないことを `ps` で確認した。精度の全件測定は CI の accuracy に任せる方針のため、結果は使っていない。
- 以後は位置引数で 1 枚ずつ流した。

## 変更されたファイル
- この確認でのコードの変更は無し（dice.py は一時変更のあと元に戻し、差分 0）。
- `git status --short` の結果は `?? archives/agents/TODO-079/review2-report.md`（最初から未追跡）と、この報告ファイル `archives/agents/TODO-079/verify-report.md`。

## 確かめられなかったこと・判断できなかったこと
- 報告ファイルの追加は、この確認の担当が作ったもの。コミットは管理者が判断する。
- 「実害」の判断はしていない。項目 1・2 以外のサンプルの結果（ポイントの誤り）は、今回の範囲外として記録だけした。
