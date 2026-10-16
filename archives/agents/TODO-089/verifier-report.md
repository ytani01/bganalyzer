# TODO-089 確認の報告（verifier）

対象: 作業ツリー（ブランチ claude/todo-089、コミット debcfbb）。サーバーは `uv run uvicorn app:app --app-dir analyzer --port 8011`（analyzer 0.54.0、recognizer 0.23.0、確認後に停止）。
スクリプト: `archives/agents/TODO-089/check_numbers.py`（Chromium、viewport 390×844、サンプル screen1）。
終了コード: 0。

## 項目ごとの結果

| 項目 | 期待 | 実測 | 一致 |
|---|---|---|---|
| white の番（左上から時計回り 24 個） | 24, 23, …, 1 の順 | `24 23 22 … 2 1`（24 個） | はい |
| black の番（同じ順） | 1, 2, …, 24 | `1 2 3 … 23 24`（24 個） | はい |
| 同じ位置の white+black の和 | 全部 25 | 全 24 個とも 25 | はい |
| 長押し（右クリック）のパレット見出し、white | 「ポイント 24」（左上の text.num と同じ） | `ポイント 24` | はい |
| 長押し（右クリック）のパレット見出し、black | 「ポイント 1」（左上の text.num と同じ） | `ポイント 1` | はい |
| black で解析、ダイス | 4-2 | `[4, 2]` | はい |
| 最善手の 1 行目 | 手番 black の表記 | `24/20 13/11` | — |
| result-svg の番号 | board の black の番と同じ | 1〜24 の順で board の black の番と完全一致 | はい |
| 最初の移動元 24 の位置に black の駒 | points[24−24]=points[0] が負（black） | `points[0]=-1`、result-svg の該当位置の番号 `24` | はい |

エラー・alert は出ていない（`alerts=[]`）。

## 食い違い

なし。

## 確かめられなかったこと・判断が要ること

- 駒の位置は `BgApp.state.board.points`（盤の状態）で確かめた。`#result-svg` 上の黒い駒の SVG は見ていない（state が読めたため）。
- 長押しは `contextmenu`（右クリック）で確かめた。タッチの長押し（HOLD_MS の経過）は実行していない。
- 盤の番号の並び順は、上段を左から右、下段を右から左とした。
