# TODO-107 確認報告（戻るボタンを下のボタンの左へ）

対象: ブランチ `claude/todo-107-back-button`、コミット `d34dc82`（analyzer 0.62.3）。
サーバーは 127.0.0.1:8001 で起動し、確認後に止めた（PID 862685 と、その親の uv 862677。`/version` が応答しないことを確かめた）。
画面は 412x915、ブラウザは /usr/bin/chromium。手順は `tools/pi_ui_check.py` の `open_app`・`read_photo`（四隅まで）・`show_outcome` と同じ。
確認スクリプトは `/tmp/claude-649/-home-ytani-work-bganalyzer/8f84bca2-0c79-4ff5-8584-dc9dbe4ee578/scratchpad/todo107/check107.py` と `photo.py`（リポジトリの外）。

## 1. 位置と大きさ（`page.evaluate` で読み出した値）

| 画面 | `#back` の rect (x, y, w, h) | 同じ行の左の `.act` | 右端 < 左端 | 中心の差 | `#actbar` 内 / header 内 | 判定 |
|---|---|---|---|---|---|---|
| 四隅（写真読み込み直後） | 16, 861, 67.78, 44 | `#recognize` 左端 91.78 | 83.78 < 91.78（隙間 8px） | 0px | 内 / 無し | 一致 |
| 盤面（`read_photo` 後） | 16, 861, 67.78, 44 | `#analyze` 左端 91.78 | 隙間 8px | 0px | 内 / 無し | 一致 |
| 結果（`show_outcome` 後） | 16, 861, 67.78, 44 | `#speak` 左端 91.78 | 隙間 8px | 0px | 内 / 無し | 一致 |

- `#back` の高さは 3 画面とも 44px。
- `#back` の computed style は 3 画面とも min-height 44px、padding `6px 14px 6px 10px`、font-size 16px。旧 CSS の値と一致。
- 結果の画面で `#back` を押すと `#board` が見え、`#outcome` が隠れた（alerts なし）。一致。
- 写真の画面（参考）: `#actbar` は display none・高さ 0、`#back` は hidden。見えているボタンは無し。一致。

## 2. スクリーンショット（`archives/agents/TODO-107/`）

- `corners-actbar.png`: 「‹ 戻る」と「盤面を読み取る」。欠け・重なり・はみ出しなし。
- `board-actbar.png`: 「‹ 戻る」と「解析する」。欠け・重なり・はみ出しなし。
- `outcome-actbar.png`: 「‹ 戻る」と「読み上げ」（スピーカーの絵つき）。欠け・重なり・はみ出しなし。

## 3. 食い違い

位置・大きさ・動作の項目に食い違いは無い。指示の範囲の外で、確認の中で分かったこと:

- 色と枠が変わっている（指示は「大きさ」だけなので、判断は管理者）。旧: 背景 `rgba(255,255,255,.18)`、文字 `var(--accent-fg)`、枠 `rgba(255,255,255,.45)`（ヘッダーの緑の上に出す色）。新: 背景 `var(--card)`、文字と枠 `var(--accent)`。`:active` も `opacity: .8` に変わった。
- `margin-left: -6px` を消し、`font-family: inherit` と `flex: none`・`align-self: center` を足している。大きさに関係する変更は `font-family` だけで、旧の computed font は測っていない（旧版を立てていない）。

## 4. 確かめられなかったこと

- 四隅の画面で `#hdr-reuse`（「前に読み取った盤面を開く」）が出ている状態は測っていない。出すには一度読み取った後の状態が要るため。TODO.md の「代表」に入っている画面なので、ローカルで要るなら追加で確かめる。
- 旧版（ヘッダー配置）の `#back` の幅は測っていない。幅は文字で決まるため、大きさの判定は高さと padding と font-size で行った。
- 実機（スマホ）の見え方、タッチの押しやすさは確かめていない（TODO.md の「スマホ:」の行の範囲）。
- 判断が要る点は無い。色の変更が「大きさは今と同じ」の範囲に入るかは、管理者が決める。

## 5. 変更ファイル

`git status` は、この確認の前後とも変更なし（作業ツリーはクリーン）。新しく作ったのは `archives/agents/TODO-107/` の本報告と 3 枚の画像だけ。
コミット `d34dc82` の変更は TODO.md、analyzer/app.py（版）、analyzer/static/app.js（APP_VERSION）、index.html、style.css の 5 ファイル。指示の範囲（analyzer の静的ファイルと版）と合っている。
TODO.md の `- [x] 移す` のチェックは、実装後に入ったもの。
