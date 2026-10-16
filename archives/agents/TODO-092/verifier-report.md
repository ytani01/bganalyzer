# TODO-092 確認の報告（verifier）

確認日: 2026-10-17。対象: 作業ツリー（ブランチ claude/todo-092、未コミット）。サービスは `bganalyzer.service`、ポート 8000（`systemctl --user cat bganalyzer` の ExecStart）。
スクリプト: `archives/agents/TODO-092/verify_todo092.py`（1 本。`uv run -q --no-project --with playwright python` で実行、chromium は `/usr/bin/chromium`、viewport 412×915）。
終了コード: 0。

## 1. /version

`curl http://127.0.0.1:8000/version` と、スクリプトの `version` の値:

```json
{"analyzer":"0.55.0","recognizer":"0.23.0","commit":"dbbe178","samples":true,"claude":true}
```

一致。`commit` は HEAD（dbbe178）で、作業ツリーの変更は未コミットのため含まれない。

## 2. 解析の結果（初期配置・手番 white・ダイス 3-1、「手で入力」から「解析する」）

| 項目 | 測った値 | 期待 | 判定 |
|---|---|---|---|
| `#result-svg g.arrows` | 1 | 1 以上 | 一致 |
| `#board-svg g.arrows` | 0 | 0 | 一致 |
| `#board-svg g.arrows`（解析の前、手番 white のまま） | 0 | - | 参考 |

最善手は `8/5 6/5`（1 位）。

## 3. 手番による U 字形の矢印（`g.way path` の d）

解析の前に、盤（`#board-svg`）で手番を切り替えて測った。`#board-svg g.way` の数は、手番 white のとき 1。

- 手番 white の `#board-svg g.way path` の d（2 本、どちらも同じ値）:
  `M554,178 H144 A42,42 0 0 0 144,262 H534`
- 手番 black の `#board-svg g.way path` の d（2 本、どちらも同じ値）:
  `M554,262 H144 A42,42 0 0 1 144,178 H534`

違う。白は上の行（y=178）から出て、左端で回って下の行（y=262）を戻る。黒は逆。どちらも U 字形で、開いている側が右（スクリプトの盤の home は right）。

解析の後（`#result-svg`）にも `g.way` が 1 つ出た（`result_way` = 1）。仕様に反する指定は無く、報告だけ。

## 4. 結果の画面の画像

保存先: `/home/ytani/tmp/playwright-mcp/todo092-result.png`（`#outcome` の要素を撮影）。Read で見た。

- U 字形の矢印: 見える。盤の真ん中に灰色の半透明で、右端から左へ戻る U 字。右側の端に矢じりがある。
- 最善手の矢印: 見える。黄色の矢印が 2 本（8→5 と 6→5）。
- 欠けや余計なもの: 盤の内側に、ダイス（右の白い 2 つ）と駒は通常どおり出ている。U 字の矢印は駒の上・ダイスの下に見える。
- 要素撮影に由来すると思われる見え方（未確認。推定）: 画面上端の「‹ 戻る」ボタンがヘッダーに重なって見える。下端の「読み上げ」の固定バーが、その下の文（「番号は盤と同じ白の人から…」など）に重なっている。固定表示の要素が撮影の範囲に入ったためと推定する。ページの見た目の不具合かどうかは、このスクリプトだけでは判断できない。

## 測った値（まとめ）

- `version.analyzer`: 0.55.0
- `state_onRoll`: white、`state_rolled`: [3, 1]
- `result_arrows`: 1、`board_arrows`: 0（解析後）
- `board_way`: 1、`result_way`: 1
- `best_move`: `8/5 6/5`
- `dialogs`: なし（reset の confirm は使っていない。「手で入力」を使った）

## 変更されたファイルと指示の範囲

`git status`:
- `M TODO.md`
- `M analyzer/README.md`
- `M analyzer/app.py`
- `M analyzer/static/app.js`
- `M analyzer/static/board-view.js`
- `M analyzer/static/style.css`
- `?? archives/agents/TODO-092/`（新規。verify_todo092.py と reviewer-report.md、本報告）

指示の範囲と合うか:
- `analyzer/static/app.js`: `#board-svg` の scene に `move: null` を渡す（指示 1）。`APP_VERSION` を 0.55.0 に上げた（版の指示どおり）。
- `analyzer/static/board-view.js`: `drawWay` を追加し、写真でない盤に描く（指示 2）。
- `analyzer/app.py`: `__version__` = 0.55.0（指示どおり）。
- `analyzer/static/style.css`: `.way` の `pointer-events: none` を追加（盤の操作を邪魔しないため。指示の範囲内と判断。`.arrows` と同じ扱い）。
- `analyzer/README.md`: 説明の追記（文書のみ）。
- `TODO.md`: チェックが 2 つ入っている（管理者が入れたもの）。`[ ] ローカル:` の 2 行は未チェックのまま。

指示に無いファイルの変更は無い。

## 確かめられなかったこと・判断できなかったこと

- テスト全体、精度（`check_accuracy.py`）: 指示どおり確認していない（CI に任せる）。
- 「壊すと落ちるか」の確認（分岐を壊す、変更前に戻す）: 指示に無かったため行っていない。`drawWay` の分岐（手番 white/black で `sweep` と `y0/y1` を反転させる）は、確かめたのは、白と黒で d が違うことだけ（向きが逆になる形）。分岐を壊して落ちるかは見ていない。
- 矢印の見た目（太さ・色・重なり）の良し悪し: 評価していない（指示どおり）。
- スマホの実機での見え方: 対象外。
- 「戻る」と「読み上げ」が画像で重なって見える件: 撮影方法に由来するかは未確認（上の推定を参照）。実害は未確認。
