# TODO-144 確認報告（verifier）

対象: ブランチ claude/sheet-no-scroll、analyzer 0.79.1。`.sheet` に `touch-action: pinch-zoom` を追加。
コードは変更していない。

## 結果の要約

| 項目 | 前 scrollY | 後 scrollY | 判定 |
|---|---|---|---|
| 1. 8001、シート内で滑らせる | 400 | 400 | 合格（変わらない） |
| 2. 8001、シート外で滑らせる | 400 | 652 | 合格（変わった。652 は最大値で打ち止め） |
| 3. 対照（8000、シート内） | 400 | 400 | 対照として不成立。下の注を参照 |
| 3'. 対照（同じページで touch-action を inline で auto に戻す） | 400 | 652（8001）、817（8000） | 合格。修正を外すとスクロールする |
| 4. 8001、#die1 のボタン 1 つをタップ | dice[0] = 4 | dice[0] = 1 | 合格（タップした 1 になった） |

## 走らせた検証と終了コード

1. 8001 の起動: `uv run uvicorn app:app --app-dir analyzer --host 127.0.0.1 --port 8001`（バックグラウンド）。`/version` は `{"analyzer":"0.79.1",...,"commit":"3e432fc"}`。終了後、PID 1775492 を kill。`/version` が応答しないことを確認した。
2. `archives/agents/TODO-144/verify_todo144.py`: 終了コード 0。出力は `archives/agents/TODO-144/verify_todo144.out`。
3. `archives/agents/TODO-144/control_touch_action.py`: 終了コード 0。出力は `archives/agents/TODO-144/control_touch_action.out`。

### 各項目の値（verify_todo144.out より）

- 8001 のシート（#sheet-roll）の矩形: x 0, y 480.5, w 412, h 250.5。盤面図（#board-svg）の下端は scrollY 400 で約 419。
- 項目 1: 点 (206, 606)、`elementFromPoint` は `sheet-roll`。before 400、after 400。
- 項目 2: 点 (206, 440)、`elementFromPoint` は `DIV#editor-title`（盤面図の下でシートの上）。before 400、after 652。
- 項目 3（8000）: 点 (206, 606)、`elementFromPoint` は `sheet-roll`。before 400、after 400。
- 項目 2 の 8000: 点 (206, 440)、`DIV#editor`。before 400、after 817。
- 項目 4: `#die1 button` の data-n は 1〜6。before 4、タップした 1、after 1。

### 項目 3 の注（重要）

8000 は別の checkout ではなく、この作業ツリー（`/home/ytani/work/bganalyzer`、ブランチ claude/sheet-no-scroll）を読んでいる。
そのため 8000 も修正後の style.css を配っている。8000 のページのヘッダーは `a0.79.1 · r0.27.2（サーバーは 0.79.0。再起動が必要）` と出る。
つまり 8000 は「修正なしの main」ではない。対照として使えなかったのは、このためである。

代わりに control_touch_action.py で、同じページの `#sheet-roll` に `style.touchAction = "auto"` を inline で入れて、修正を外した状態を作った。
結果は次のとおり（control_touch_action.out）:

- 8001、配られた CSS のまま: before 400、after 400。computed の touch-action は `pinch-zoom`。
- 8001、inline auto: before 400、after 652。
- 8000、配られた CSS のまま: before 400、after 400。computed は `pinch-zoom`。
- 8000、inline auto: before 400、after 817。

この対照で、シート内でスクロールが止まるのは `touch-action: pinch-zoom` によるものだと確かめられた。

## 測り方の変更（途中で行ったこと）

- `Input.synthesizeScrollGesture`（gestureSourceType touch）は、8000 の対照でも scrollY を動かさなかった。そのため測れていなかった。
  `archives/agents/TODO-144/` での試し（debug スクリプトは削除済み）で、`Input.dispatchTouchEvent` の touchStart / touchMove（10 段）/ touchEnd は scrollY を動かすと確かめた。
  以後の測定はすべて dispatchTouchEvent で行った。
- 最初の測定は scrollY 200 で行った。盤面図の下がシートの上に出て、「シートの外・盤面図より下」の点を取れなかった（点 (206, 440) は盤面図の上に当たった）。
  scrollY 400 にそろえ直し、盤面図の下端（約 419）とシートの上端（480.5）の間の帯を使った。
- 各スワイプの前に scrollY を 400 に戻した。戻さないと、先の操作で最大値に当たって、後の測定が意味を持たなくなるため。

## 変更ファイルと指示の範囲

`git diff main --stat`:
- TODO.md（1 行の変更。内容は未確認）
- analyzer/app.py（版の数字）
- analyzer/static/app.js（APP_VERSION の 0.79.0 → 0.79.1。analyzer の版を上げる決まりどおり）
- analyzer/static/style.css（1 行追加: `.sheet` の `touch-action: pinch-zoom`）

作業ツリーの未追跡: `archives/agents/TODO-144/`（このための報告とスクリプト）。
指示に無いファイルの変更は無い。

## 確かめられなかったこと・判断できないこと

- 実機のスマホ（タッチ操作の慣性スクロールや、実際の指の操作）は確かめていない。合成のタッチ入力での確認である。
- `preventFling: true` は使っていない（dispatchTouchEvent は慣性を起こさない）。慣性つきのスワイプでの挙動は見ていない。
- 「シートの外」は、盤面図の下でシートに重ならない帯（scrollY 400 で y 約 420〜480）で測った。境界線上の判断（盤面図とシートの境目、シートの上端ぎりぎり）は行っていない。
  境界線上の挙動は実害は未確認で、報告だけにする。
- 8000 は修正の入った作業ツリーを配っているため、「修正なしの main」との比較は、inline auto による対照で代用した。本物の main（0.79.0 の CSS）を別に用意してはいない。
- シート内で指が盤面図やボタンの上にある場合の、ボタンの押下とスクロールの関係は、項目 4（タップ）以外では見ていない。
- ほかのシート（match・cube）は見ていない（指示どおり）。
