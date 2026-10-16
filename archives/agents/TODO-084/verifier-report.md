# TODO-084 確認報告（verifier）

対象: ブランチ claude/todo-084-fix-corners-impl（HEAD 1dc39d3）。コードは変更していない。
`git status` の変更は `archives/agents/TODO-084/` の追加だけ（追跡ファイルの変更なし）。

## 1. `uv run pytest analyzer/test_photo_view.py -q`

- 結果: 12 passed, 1 warning（starlette の httpx 非推奨の警告）。終了コード 0。

## 2. `uv run python archives/agents/TODO-084/measure_keep.py photo6`

- 出力: `photo6	18	14`（終了コード 0）
- 期待値 `photo6	18	14` と一致。README の表（photo6: 合わせ直す 18、固定する 14）とも一致。

## 3. PWA を Playwright で操作（`archives/agents/TODO-084/check_ui.py`）

サーバーは `uvicorn app:app --app-dir analyzer --host 127.0.0.1 --port 8765`（PID 516812）。
起動時の `/version`: analyzer 0.50.0, recognizer 0.23.0, commit 1dc39d3。
確認後に PID 516812 を kill し、停止を確かめた。8000 の常駐（PID 509018）には触れていない。
画面 412x915、Chromium は /usr/bin/chromium、写真は samples/screen2.jpg（1080x2160、送信時は 2048 に縮小）。

| 項目 | 測った値 | 期待 | 判定 |
|---|---|---|---|
| a. 新しい写真を選ぶ | keep=False（checkbox=False）、cornerGuess=`finding` | 外れている | 一致 |
| b. 「四隅をやり直す」→ canvas の 4 点を `page.mouse.click` | keep=True（checkbox=True）、corners 4 点、cornerGuess=``、cornersMoved=True | 入る | 一致 |
| c. 正解の四隅を update → 読み取り | sent と geometry.corners の最大差 0（8 座標とも 0）、state.corners との最大差 0 | 1px 未満 | 一致 |
| d. 戻る → チェックを外す → 読み取り | sent と geometry.corners の最大差 17.5（TL dx4.4 dy14.2 / TR dx17.5 dy9.7 / BR dx13.7 dy4.1 / BL dx5.6 dy8.6） | 1px 以上 | 一致（keep はクリック前 True、後 False） |
| e. 同じ写真を選び直す（チェックが入った状態から） | keep=False（checkbox=False）、cornerGuess=`finding` | 外れている | 一致 |

各項目の alerts は空。実行は 2 回。1 回目は d のあとの e のクリックで、非表示（board 画面）のため timeout した。2 回目（スクリプトの修正後）は全項目完走。この 1 回目と 2 回目の差は、スクリプト側の操作手順の誤りで、アプリの挙動の問題ではない。

スクリプトからの逸脱（期待どおり確かめるための操作）:
- チェックボックスは `<label>` の中にあり、input 単体は見えないため `label:has(#keep-corners)` をクリックした（実際のユーザー操作に相当）。
- 読み取り後の画面は board なので、e の前に `#back` で corners 画面に戻ってからチェックを入れた。
- 「d の後に e」を成立させるため、e の前にチェックを入れ直した（指示の a〜e の順番は守った）。

## 変更ファイルと範囲

`git diff --stat main...HEAD`（10 files, +101 −31）:
TODO.md, analyzer/README.md, analyzer/app.py, analyzer/static/app.js, analyzer/static/index.html, analyzer/static/scan.js, analyzer/test_photo_view.py, docs/PI_CHECKS.md, recognizer/README.md, recognizer/board.py

- すべて「四隅を固定する」の範囲に含まれる。
- analyzer/static/scan.js は 1 行のコメントの追記だけ（fit の段数に「四隅を固定したときは 1 回」）。
- analyzer/app.py は `keep_corners` の Form 引数と recognize への受け渡しだけ。
- 範囲外のファイルは無し。diff の中身までは、指示の項目以外は見ていない（TODO.md・docs/PI_CHECKS.md は stat のみ）。

## 確かめられなかったこと・判断が要ること

- 「もう一度検出」と Claude の四隅でチェックが外れること（指示どおり、コードを読むだけで済ませる対象。実測はしていない）。
- 全サンプルの精度（CI の対象。見なくてよいとの指示に従った）。
- 判断は要らない。すべての測定値は指示の期待と一致した。
