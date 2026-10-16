# TODO-090 確認（verifier）

対象: worktree `/home/ytani/work/bganalyzer-090`（未コミット）、サーバー `http://127.0.0.1:8090/`（版 `a0.56.0 · r0.23.0` を画面ヘッダーで確認）。
スクリプト: `archives/agents/TODO-090/verify_todo090.py`（1 本）。測った値の全文: `archives/agents/TODO-090/verify_todo090.out.json`。
実行: `uv run -q --no-project --with playwright python archives/agents/TODO-090/verify_todo090.py`（chromium は `/usr/bin/chromium`、viewport 412x915）。終了コード 0。

手段の注意: 2・3 の一部の操作（進む `.seg` ボタン、ダイス、キューブの選択、「盤に戻る」）は Playwright の `click` では「見えない」と判定されたため、同じ `click` / `change` イベントを DOM 上で発火させた。ボタンの操作は実際のタップと同じハンドラを通る。

## 1. 盤の PIP 札と「バー」の文字

- 初期配置（`#manual`）の `#board-svg text.pip-n`: `["PIP 167", "PIP 167"]`。`BgBoard.pips` も `{white: 167, black: 167}`。一致。
- 盤の最初の `rect.hit` を 1 回タップ。点の配列は `[..., 5, 0, 3, 0, 0, 0, -5, 3, ...]`（点 13 の白が 5 → 3 に変わった）。
  PIP 札は `["PIP 141", "PIP 167"]`、`BgBoard.pips` は `{white: 141, black: 167}`。タップで数が変わり、盤の数と JS の値が一致。
- 「バー」の文字: `#board-svg` 内に「バー」を含む text は 0 件（初期配置・タップ後・結果の盤のいずれも 0 件）。

## 2. 結果の画面の並び（初期配置・白・ダイス 3-1）

`#result` の直下の要素（上端の y 座標、画面上の px）:

| 順 | 要素 | 中身（先頭） | top |
|---|---|---|---|
| 1 | `p.summary` | 白が有利: 勝率 52.5%… | 431 |
| 2 | `div.winbar` | 白 52.5% / 黒 47.5% | 481 |
| 3 | `h2` | 最善手（白・ダイス 3-1） | 517 |
| 4 | `ol.moves` | 8/5 6/5 … | 552 |
| 5 | `p.note` | 番号は盤と同じく… | 725 |
| 6 | `table` | 白黒 勝率 52.5% 47.5% … | 777 |
| 7 | `p.note` | gnubg 2手読み… | 970 |

上の 4 つ（summary → winbar → 最善手の h2 → table）は指示どおりの順。一致。

`/analyze` の応答 `pips`: `{white: 167, black: 167}`（HTTP 200）。`#result-svg text.pip-n`: `["PIP 167", "PIP 167"]`。一致。
ただし初期配置は両方とも 167 なので、どちらの色の札がどちらの数かは、この局面では区別できない（判断ではなく、この局面で測れなかったこと）。
`#result-svg g.arrows` = 1、`g.way` = 1。

## 3. キューブの判断の局面（ダイス無し）

- 3a（指示どおり: 手番 white・ダイス空・キューブ centre）: `/analyze` は HTTP 200、`cube` あり、`moves` なし。
  結果の並び: `p.summary`(431) → `div.winbar`(502) → `h2` 「キューブ」(538) → `p.answer` 「白の人は ダブルしない」(573) → `p` 「ダブルされたら、黒の人はテイク。」(619) → `table`(659) → `p.note`(792) → `table`(824) → `p.note`(1017)。
  最善手の代わりに「キューブ」が同じ位置に出る。一致。
  注意: 3a のキューブの状態は `{at: "centre", value: 2, offered: true}`。私は `offered` を操作していない（2 の画面から引き継がれた状態）。`at` が centre でも `offered` が true のまま解析されている。
- 3b（参考: キューブを白に置き、ダブルされた状態で黒が手番。`offered` を true に設定）: 同じ順（summary → winbar → 「キューブ」→ answer → p → table → note → table → note）。`answer` は「白の人は テイク」。一致。

## 4. 結果の盤の撮影

`~/tmp/playwright-mcp/todo090-result.png`（`/home/ytani/tmp/playwright-mcp/todo090-result.png`）は 2 の状態の `#result-svg`。Read で見た範囲:

- PIP の札: 上（黒、暗い札）に「PIP 167」、下（白、明るい札）に「PIP 167」。どちらも盤の右端、トレイの横にあり、欠けや重なりは無い。
- U 字形の矢印: 灰色の U 字が盤の上半分を回って中央の矢印で終わる形で出ている（白の手番の進み方）。欠けは見えない。
- 最善手の矢印: 黄色の矢印 2 本（点 8 → 5、点 6 → 5）。`8/5 6/5` の手と合う。
- 余計なもの: 見当たらない。キューブ（「64」、下の左）が白の PIP 札の左に離れて出ている。ダイス（3 と 1）は中央右に出ている。
- 「バー」の文字は見えない。
- 画像は小さく（約 370px 幅）、細部の文字は読みにくい。デザインの良し悪しは評価していない。

## 判断が要る点

- 3a で、キューブが centre のまま `offered: true` が残っている。指示の「キューブを中央にして」を満たす状態ではあるが、`offered` の残り方が意図どおりかは管理者が確かめてほしい（実害は未確認）。
- 2 の PIP の一致は、両方 167 の初期配置でしか測っていないため、色と数の対応までは確かめられていない（実害は未確認）。

## 確かめられなかったこと

- テスト全体、精度（CI の担当）。
- 他の局面、他のボタン、コードの修正、原因の切り分け（範囲外）。
- 盤のタップ後の結果の画面で、PIP 札と `/analyze` の値が一致するか（今回は初期配置のみ）。
