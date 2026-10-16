# TODO-088 verifier の報告

条件: 390×844、is_mobile・has_touch、screen1。サービスは `/version` が analyzer 0.53.0・recognizer 0.23.0（再起動は不要だった）。
スクリプト: `archives/agents/TODO-088/verify.py`（終了コード 0）。画像: `/home/ytani/tmp/playwright-mcp/todo088-verify/`。コードは直していない。

## 結果（食い違いは無し）

1. 写真の選択: 「うまく読み取るコツ」の上端 218px、3 つのボタンの下端はいずれも 206px。コツが下。OK
2. 四隅の画面
   - 説明は「点を動かして盤の内側の四隅に合わせてください。」、高さ 23px = 行の高さ 23px で 1 行。OK
   - 「四隅を固定する」の行の中身はそれだけで、次の要素は「手前のホーム」。注記なし。OK
   - 真っ黒な 800×600 の画像: cornerGuess は `default`。説明は「盤を見つけられませんでした。点を動かして盤の内側の四隅に合わせてください。盤が小さいときは「その他」の「画像を編集」で切り抜いてください。」（4 行）。OK
   - 画面を自分で見た（`2-corners.png`）: 欠け・重なり・余計なものなし
3. 盤面の画面
   - 写真の中ほどをタップ: 盤面は変わらず、吹き出しも出ない。`#photo-svg .hit` は 0 個。OK
   - 盤のポイントのタップ（`#board-svg .hit` の 1 つ目）: 盤面が変わった。OK
   - 長押し（マウスを 800ms 押す。HOLD_MS は 450）: `#palette` が出て、題は「ポイント 19」、ボタンは「白」「黒」。OK（数のボタンは読んでいない）
   - `[class*=loupe], [id*=loupe]` は盤面の画面で 0 個、長押しの最中も 0 個。OK
   - 画面を自分で見た（`3-board.png`、`3-hold.png`）: 欠け・重なり・余計なものなし
4. 「解析の設定」の並び（cube を白にして測った上端）: キューブ 494、ダブルされたところ 610、振った人 674、ダイス 714。キューブ → ダブルされたところ → 振った人 → ダイス。OK
   - 「入れ替える」ボタン（折りたたみの外）は 0 個、`#flip-turn` は無い。OK
   - キューブを白に置くと `#dice-row` は display:none。「ダブルされたところ」を外すと display:flex で戻る。OK
5. 数のずれ
   - 合っているとき: `#count-mark` は hidden で空、`#errors` も空、「盤上とバー」「上がり n」の文は無い。OK
   - 白を 1 個減らす: 「⚠ 白 14/15」。盤の下端 724px、印 732〜753px、`#editor` 759px。`#board-pin` の中。`#errors` は hidden で空。OK
   - 元に戻す: hidden に戻り空。OK
6. 「写真」の印: 読み取った直後、`#dice-note`（ダイスの横）と `#cube-note`（キューブの `.seg` の隣）が出て、文は「写真」。`die1` を変えるとダイスの方だけ hidden になり、キューブの方は残る。OK

## 変更されたファイル

`git status`: TODO.md、analyzer/README.md、analyzer/app.py、analyzer/static/{app.js,board-view.js,index.html,style.css,sw.js}、tools/ui_snapshot.py、archives/agents/TODO-088/（未追跡）。implementer の報告と合っている。指示に無いファイルの変更は無し（範囲が妥当かの判断は管理者）。

## 確かめられなかったこと・補足

- 長押しは、実機の指ではなく Playwright のマウス（touch の emulation 下）で再現した。実害は未確認だが、スマホの実機の長押しは「ローカル:」「スマホ:」の確認に残る
- 盤のタップは「変わった」ことだけを見て、置く段までは見ていない
- 数のボタン（パレットの駒の数）は押していない
- 四隅の画面（真っ黒な画像）は screenshot を撮ったが開いて見ていない（2-corners-black.png）。テキストの測定のみ
