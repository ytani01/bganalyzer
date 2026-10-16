# TODO-097 / TODO-098 確認報告（verifier）

対象: branch claude/todo-097-098、コミット c5bbdb9。コードは変更していない（一時的な書き換えは `git checkout -- analyzer/engine.py` で戻し、`git status` はきれい）。

## 1. テスト
- `uv run pytest -q analyzer/test_pwa.py`: 25 passed, 終了コード 0
- `uv run pytest -q analyzer/test_api.py -k "luck or cube"`: 9 passed, 39 deselected, 終了コード 0

## 2. analysis.analyze の測定
- 初期局面 `4HPwATDgc/ABMA`、dice (3,1)、plies=1: luck = 0.163（指示の +0.163 付近に一致）
- 初期局面、dice (6,6)、plies=2: luck = 0.329（0.3 より大きい。一致）
- 初期局面、dice なし、plies=1: luck = None（一致）

## 3. テストが壊れを捕まえるか（engine.py の `_luck` を一時的に壊す）
- (a) 重み外し（`* (1 if r[0] == r[1] else 2)` を削除、`/ 36` を `/ 21`）: `test_api.py -k luck` は失敗（1 failed）。落ちた箇所は `test_luck_of_the_roll` の `analyzer/test_api.py:452`:
  `assert -0.023916666666666666 == 0 ± 0.002`（平均が 0 になる、の検査）。
  - 注: 直前の実行で終了コードを `PIPESTATUS` で取ろうとして空になった。落ちたことは出力で確認済み。
- (b) 盤の入れ替えを外す（`-gnubg.evaluate((b[1], b[0]), c_opp, ctx)[5]` を `-gnubg.evaluate(b, c_opp, ctx)[5]`）: 失敗（終了コード 1）。落ちた箇所は `analyzer/test_api.py:460`:
  `assert ([] == []  ... Use -v ...  0.468 < 0)`（ダンス＝動かせない目の luck が負になるべきところが +0.468）。
- 両方とも戻して `git status` がきれいなことを確認。

## 4. PWA（ポート 8767、Playwright、390x844、chromium /usr/bin/chromium）
- `/analyze` の応答: status 200、luck = 0.329
- `BgResult.html`: 「最善手（白・ダイス 6-6）」の見出し（位置 189）の後、`<p>Luck +0.329・良い目</p>`（位置 215）、`<ol class="moves">`（位置 234）の前。順序は正しい。
- `BgResult.speechText`: 「白の人、ダイス 6 6の最善手は、24から18を2つ、13から7を2つ。良い目です。ほぼ互角です。」— 「良い目です。」を含む。
- 立てた 8767 のサーバーは停止済み。常駐の 8000（bganalyzer.service）には触れていない。

## 食い違い
- なし。

## 確かめられなかったこと・判断が要る点
- (a) の終了コードは取り損ねた（出力で失敗は確認）。
- 一時ファイルは `/tmp/x`（engine.py の写し）を作ったが、その後 `rm -f` で消した。スクラッチパッド外に作ったのはこの 1 件のみ。
