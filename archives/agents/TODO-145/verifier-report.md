# TODO-145 確認の報告（verifier）

対象: /home/ytani/work/bganalyzer-145（ブランチ claude/remove-paint-side、HEAD f549d92）。コードは変えていない。

## 準備

- サーバー: `uv run uvicorn app:app --app-dir analyzer --host 127.0.0.1 --port 8002` をバックグラウンドで起動。`/version` は `{"analyzer":"0.80.0","recognizer":"0.27.2",...}`。
  終わったあと uv の PID 1779925（子の python 1779948）を `kill` で止め、ポート 8002 が応答しないこと、プロセスが無いことを確かめた。
- ブラウザ: 最初は `connect_over_cdp("http://127.0.0.1:9222")` で新しいコンテキスト（412x848）を開いた。既存のタブは操作していない。
  **注意:** 測り終えて `browser.close()` を呼んだあと、9222 は応答しなくなった（`curl` が無応答、`tools/live_view.py` のプロセスも無く、リッスンしているポートも無い）。
  閉じたのが自分の `browser.close()` か、別の理由かは確かめられていない。live_view の再起動は利用者の判断に任せた。

## 項目ごとの結果

スクリプト: `/home/ytani/work/bganalyzer-145/archives/agents/TODO-145/verify_145.py`（項目 1〜4）。
項目 5 の記録: `/home/ytani/work/bganalyzer-145/archives/agents/TODO-145/snapshot-after.json`（ログ `record.log`）。

| 項目 | 結果 | 測った値 |
|---|---|---|
| 1. `#paint-side` が DOM に無い | PASS | count=0 |
| 2a. 同じ行（縦の範囲が重なる） | PASS | #editor-title 438.5〜477.5、#undo 436〜480。重なり 39px |
| 2b. #undo が右端 | PASS | #editor.right 381、#undo.right 370。差 11px = padding-right 10px + border 1px |
| 2c. #undo が 1 行 | PASS | white-space: nowrap、高さ 44px、line-height: normal、font-size 15px。Range の矩形は 1 段 |

- 2 の追加: `#editor-row` の flex-wrap は nowrap。#editor-title は 2 行に折り返し（高さ 39px）。説明の文は `#undo` と並んで読めて、重なりは無い。
- 2 のスクリーンショット: `/home/ytani/work/bganalyzer-145/archives/agents/TODO-145/editor-412x848.png`。説明の文は 2 行で欠けず、「元に戻す」は右端にあり、はみ出しも重なりも見えない（「元に戻す」は押せない状態の淡い表示）。
- 3. 空のポイントに黒: PASS。右クリックで palette を出し、黒と数 0 を押し、別の空のポイント（points の index 14、before 0）をクリック。after −3、変わったのは index 14 だけ、palette は閉じた。
  観察: 数 0 を選んでも置く数は固定ではなく、中央クリックで 3 個になった。黒が置かれる（負）という条件は満たしている。
- 4. #undo で戻る: PASS。タップの直前の points と #undo 後の points が完全に一致（差分 0）。
- 5. `BG_URL=http://127.0.0.1:8002/ tools/ui_snapshot.py record`: PASS。終了コード 0、64 snapshots を書き出した。
  「奥's colour on an empty point」の boardSvg で、x=140（hit 2）の黒の駒が 0 → 2 個になった（直前の「tap an empty point」と比べた）。その点が黒になっている。

## 変更ファイルと指示の範囲

`git diff main...HEAD` で 7 ファイル（+11 −21）。指示の範囲と合っている。
- `analyzer/static/index.html`: #paint-side とその行を削除、#undo を .editor-row の右端へ。
- `analyzer/static/style.css`: .editor-row の折り返しを外し、.undo に nowrap。`.paint-side` の規則は残る。palette 側の `#palette-side` が同じクラスを使うため（dead ではない）。
- `analyzer/static/app.js`: paintSide の表示と click の処理を削除、APP_VERSION を 0.80.0。
- `analyzer/app.py`: version 0.80.0。
- `tools/ui_snapshot.py`: paintSide の記録を削除、奥の色の手順を長押しと色の選択に変えた。
- `analyzer/README.md`: 「空の所に置く色」の 1 文を直した。指示の範囲の外ではなく、文書の追随。
- `TODO.md`: チェックの入れ替え（実装時に入れたもの）。

作業ツリーに残っている未追跡のファイルは `archives/agents/TODO-145/` のみ（このフォルダに作ったスクリプト、画像、記録、この報告）。

## 確かめられなかったこと・判断が要る点

- **判断が要る点: 9222 の Chromium が応答しなくなった。** 原因は自分の `browser.close()` かもしれないし、確かめていない。`tools/live_view.py` の再起動が要るかは利用者が決める。
- 2 は 412x848 の 1 条件だけ。狭い幅での折り返しは見ていない（依頼の範囲外）。
- 項目 5 の記録では、palette を開いたのとタップしたのが同じ点（hold(2) → tap(2,2)）。「別の空の点」の確認は項目 3 で行った。
- デザインの良し悪し、ほかの画面、精度、テスト全体は見ていない（依頼どおり）。
