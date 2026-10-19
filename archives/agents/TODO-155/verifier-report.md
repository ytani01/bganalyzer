# TODO-155 verifier の報告（PR #461、コミット 0d22a81）

測り方: 8765 番で起動した PR のコード（版 a0.87.0 · r0.28.0）を、live_view のブラウザ（CDP 9222）の新しいページ
（390×844）で開き、`screen-app-grey-shot` を読み取って盤面の画面へ進めた。`BgApp.update` でマッチとキューブを設定し、
盤の横の列（左側が home）を CDP の `Page.captureScreenshot`（3 倍）で撮って画像を見た。
スクリーンショットは `~/tmp/playwright-mcp/todo155-*.png`（`-col` が列、`-full` が盤全体）。

| 項目 | 結果 |
|---|---|
| 1. マッチ 5 点、スコア 2 対 3、キューブ中央 | 合っている。スコアはグレーで角の無い四角（奥 3 / 手前 2）。PIP は列の上端（PIP 160）と下端（PIP 167）に「PIP」と数字の 2 行。キューブ・ゴール・スコアと重ならず、欠けなし。`todo155-match-centre-*.png` |
| 1. 同、奥がキューブを持つ | 合っている。奥のキューブ（2）が PIP の下、奥のゴールの上にあり、重ならない。`todo155-match-black-*.png` |
| 1. 同、手前がキューブを持つ | 合っている。手前のキューブ（2）が手前のゴールと PIP の間にあり、重ならない。`todo155-match-white-*.png` |
| 1. 盤の上に古い PIP の札が残っていないか | 残っていない。盤全体の画像（`todo155-match-centre-full.png`）で盤の上に札なし。`#board-svg` の text も `PIP`・`167`・`PIP`・`160` の 4 つだけで、`PIP 167` の形は無い |
| 2. アンリミテッド、キューブ中央 | 合っている。スコアは出ず、キューブ 64 は列の中央、PIP は上下に出て崩れなし。見出しは「アンリミテッド ▾」。`todo155-money-centre-*.png` |
| 3. PIP をタップ（1 回） | 持ち主は入れ替わった。札の色（暗↔明）、石の色、PIP の数が変わった。**ただし数字そのものが入れ替わったのではない**: 奥 160 / 手前 167 → 奥 208 / 手前 215（`BgBoard.pips` も white 167→215、black 160→208）。`todo155-after-tap-col.png`。この PR の差分は `swapColours` に触れていない（`git diff --stat`）。「数字が入れ替わる」が 160↔167 の意味なら食い違い。実害は未確認。切り分けはしていない |
| 4. 結果の画面（解析後） | 同じ列が出ている。スコア 3 / 2、キューブ 64、PIP が上下（タップ後の状態: 奥 208 / 手前 215）。ベストムーブの矢印と重ならない。`todo155-outcome-col.png`、`todo155-outcome-full.png` |

## ほか
- コンソールのエラーは無し。警告は 1 件のみ（`apple-mobile-web-app-capable` が非推奨）で、この PR とは無関係と思われる（推定）。
- 変更ファイルの範囲の確認は依頼に無かったので、`git diff --stat origin/main...HEAD` を見ただけ:
  TODO.md、analyzer/README.md、analyzer/app.py、analyzer/static/{app.js,board-view.js,style.css}、archives/agents/TODO-155/implementer-report.md。
- 確かめていない: 右側が home のとき（`sideX(home)` の右側）、キューブが offered のとき、2 桁・3 桁の PIP 数（167 の 3 桁は確認済み）、
  実機のスマホ。色合いとデザインの良し悪しは依頼の対象外。
- 後始末: 8765 番のサーバーを止め、worktree `.claude/worktrees/todo155-verify` を消した。コードは変更していない。
