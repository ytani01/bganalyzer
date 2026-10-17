# TODO-112 確認の報告

対象: claude/todo-112-board-settings（HEAD b124ae4）。コードは変更していない（`git status` は空）。
確認の道具: scratchpad の `verify112.py`（手順 1〜3）、`tools/pi_ui_check.py speech`（手順 4）。
8001 は保存先 collected112 付き、8002 は環境変数なしで自分が起動し、PID（uv 912467、uvicorn 912472）で止めた。

## 手順ごとの結果

1. 8001、新しいページ（localStorage 空）、screen1 を読み取り、「解析する」
   - 期待: `#improve`・`#collect-opt`・`#export-opt` が見える／保存するに `on`／POST /samples が 1 回 200／collected112 に 2 ファイル増える
   - 実際: `#improve` block（高さ 278）、`#collect-opt` block、`#export-opt` block。seg は `on` が保存する、`off` が保存しない。POST /samples 1 回、200。増えたのは `user-1792215507138-yo3g6c.png` と `.truth.json` の 2 ファイル。確認後に削除し、残りは 0。
   - 一致

2. 8001、写真なし、「手で入力」から盤面の画面へ
   - 期待: `#improve` が display none
   - 実際: `#improve` display none（高さ 0）。`#collect-opt`・`#export-opt` も display none。盤面の画面（`#board`）は表示されている。collected112 の変化なし。
   - 一致

3. 8002、写真を読み取り、「解析する」
   - 期待: `#collect-opt` が隠れ、`#export-opt` が見える。`/samples` への要求なし
   - 実際: `#collect-opt` hidden（display none）、`#export-opt` block（高さ 91）、`#improve` は block。`/samples` への request は 0 件。response も 0 件。新しいファイル 0。
   - 一致

4. `BG_CDP=http://127.0.0.1:9222 BG_URL=http://127.0.0.1:8001/ uv run -q --no-project --with playwright python tools/pi_ui_check.py speech`
   - 期待: OK、collected112 のファイルが増えない
   - 実際: `OK   speech: spoken=['白の 4 2 の最善手は、8から4、6から4です。', 'ほぼ互角です。'] alerts=[]`。collected112 は実行の前後とも 0 件。
   - 一致
   - 注意: `| tail` を挟んだので Python の終了コードは取っていない。`OK` の行が出て、スクリプトは失敗 0 のとき 0 を返す作りなので、終了コード 0 と読んでいるのは推定。

## 食い違い

なし。

## 判断できなかったこと・残る注意（判断は管理者）

- 手順 4 の `pi_ui_check.py` の INIT は、localStorage の `collect` が空なら `off` を入れる。そのため手順 4 は「既定の on のとき保存しない」を試していない。既定の on は手順 1（空の localStorage で `on` のクラス、保存の 200）で確かめた。手順 4 の確認に、そのことを足すかどうかは判断が要る。
- 手順 4 のあとに live_view の窓（9222）を確かめると、`localStorage.getItem('collect')` は `null` だった（別タブで読んだ値）。ただし読んだのは 1 回だけ。
- 手順 4 の `pi_ui_check.py` は最後に `browser.close()` を呼ぶ。9222 の `/json/version` は、実行の後も応答した。live_view の窓が閉じていないかは、画面を見て確かめていない。
- 手順 2 で `#improve` が display none になる理由（CSS の規則か、子が無いことによるものか）は調べていない。期待どおりの値だけ確かめた。
- 8002 の起動は `uv run` で行い、止めたのは uv（912467）と uvicorn（912472）。両方とも終了を確かめた。
