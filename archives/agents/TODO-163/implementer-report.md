# TODO-163 implementer の報告

## 変更点

- `analyzer/static/board-view.js:23-24` `COL.w` を 56 → 43。根拠: キューブ 40 ＋ 縁の線 2.5（外へ 1.25 ずつ）= 42.5 を収める最小の整数。ピップ数は "888"（3 桁の上限の目安）を 20px bold で測って 33.3〜34.6（Chromium、幅 390 と 1280）で、キューブより細いので列の幅を決めない
- `analyzer/static/board-view.js:81-82` viewBox の横を詰めた。左右とも、盤の枠・列の外にトレイの線（幅 4）の外側の分 2 だけ残す。
  home=right: `12 … 683`（前は `0 … 724`）、home=left: `-39 … 683`。縦（上下の 4 とマッチの行）は変えていない
- `analyzer/static/style.css:180-181` `.board-wrap` の左右の padding を 0 にし、`margin-inline: -16px` で `main` の左右の padding の上まで広げた（上下の padding 4px は残す）
- `analyzer/static/style.css:197-198` 1000px 以上で写真と盤面を並べるときは、内側（写真の右・盤面の左）の負のマージンを 0 に戻す（2 枚が grid の gap 8px を挟んで重ならないように）
- 座標の依存: `sideX`・`trayY`・`scoreY`・`cubeY`・`pipY`、取ったチェッカー（`COL.w - 12`）、ピップ数・点数の文字（`COL.w / 2`）、キューブ（`(COL.w - size) / 2`）、矢印の `off` の終点（`sideX` ＋ `COL.w`）、トレイの当たり判定（`width: COL.w`）は、すべて `COL.w` から計算していて書き換え不要だった。`660` を直書きしていたのは viewBox の 1 か所だけ
- `analyzer/app.py:33`・`analyzer/static/app.js:14` 0.89.3 → 0.90.0
- `TODO.md` の TODO-163 の実装の 3 行にチェック

## 測った値（headless Chromium、`/usr/bin/chromium`、#manual で開いた盤面）

| 幅 | | 盤面図の左端 | 盤面図の横幅 | 枠（628 単位）の画面上の幅 |
|---|---|---|---|---|
| 390 | 前 | 20 | 350 | 303.6 |
| 390 | 後 | 0 | 390 | 358.6 |
| 1280 | 前 | 300 | 680 | 589.8 |
| 1280 | 後 | 280 | 720 | 662.0 |

390 で `document.documentElement.scrollWidth` = 390（横スクロールは出ない）。
home=left / right の両方で、取ったチェッカー 10・12 個、点数 5・3、キューブ 4（奥の持ち）、ピップ数、`off` への矢印を描いた絵を見て、欠け・重なりが無いことを確かめた。

## 検証

- `uv run pytest analyzer/test_pwa.py` → 34 passed（終了コード 0。warning 1 件は Python を触っていないので元からのもの）

## 残る懸念

- 幅 390 では盤面のカードが画面の端まで届き、角の丸み（8px）は画面の端で切れる形になる。気になるなら `border-radius` を 0 にする判断が要る
- 1000px 以上で写真と並べる形は、写真が要るので測っていない（CSS の規則だけ確かめた）。verifier に頼むこと
- 縦長のスマホで上に貼り付く `.board-pin` から盤面が左右に 16px はみ出す。`.board-pin` の背景（var(--bg)）は盤面の横には無いが、盤面自体のカードの背景で覆われるので見た目は変わらないはず（実機では未確認）
