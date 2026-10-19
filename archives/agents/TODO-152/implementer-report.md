# TODO-152 implementer report

## 変更
- `analyzer/static/board-view.js`: COL を score 32 / cube 28 / pad 3 に。`trayY`（端はキューブ分あける）、新設 `scoreY`、`cubeY`（奥持ち=COL.y0、手前持ち=COL.y1-cube、中央=奥スコアの下）。`drawMatch` は白地の 32×32 の札に数字だけ。`drawCube` は第5引数 `match` を受け、`length>0 && crawford` で `Crawford`（textLength=24、spacingAndGlyphs）。先頭近くと2関数のコメントを更新。
- `analyzer/static/style.css`: `.score-n`（20px 太字）、`.cube-crawford`（7px 太字）を追加。
- `analyzer/app.py`、`analyzer/static/app.js`: 0.85.0。
- `analyzer/static/sw.js`: CACHE v59 -> v60（TODO-089 の盤の見た目の変更 PR が同じく上げていたため）。
- `TODO.md`: TODO-152 の 1 つ目にチェック。

## 測った値（getBBox。viewBox 座標、ホームが右／左、キューブは奥・中央・手前、Crawford あり／なし、アンリミテッド）
列は y 18..422、x 650..706（右）。奥トレイ 49..168、手前トレイ 272..391、スコア札 171..203 と 237..269（x 662..694）、
キューブ 18..46 / 206..234 / 394..422（x 664..692）。間は全部 3。Crawford の字は 24×8 でキューブ内（x 666..690、y 216..224）。
アンリミテッドはスコア札なし。左ホームは x が -50 に移るだけで y は同じ。はみ出し・重なりなし。
`uv run pytest analyzer/test_pwa.py`: 31 passed。
測定は board.js と board-view.js を単独ページに読み込んで実行（実アプリ・BG_CDP は未使用）。

## 懸念
- Crawford の字は 7px 相当とかなり小さい（textLength で幅を詰めている）。見た目は未評価。
- タップの実機確認（`- [ ] ローカル:`）は未実施。

## 追加の直し: Crawford を 2 行にした
textLength で詰めるのをやめ、「Craw」「ford」の 2 行（font-size 10px、太字。以前は 7px を横に詰めていた）。
getBBox（右ホーム、キューブ x 664..692、y 206..234）: 1 行目 x 665.8..690.4、y 208.8..220.2。2 行目 x 668.3..687.7、y 219.8..231.2。どちらもキューブの内側。
12px は幅 29.7 でキューブからはみ出したので 10px。字の高さは 10（bbox の行高は 11.4）。

## 追加の直し: キューブを大きくした
配分: cube 40 / score 32（正方形のまま）/ tray 101 / 間 3（3*40+2*32+2*101+6*3 = 404）。トレイの板は高さ 4・間隔 5（以前は 5・6）。
字: Crawford 14px 太字の 2 行、cube-num 20px（以前 10px と 15px）。`analyzer/static/board-view.js`・`style.css`。
getBBox（右ホーム）: 奥持ちキューブ y 18..58、奥トレイ 61..162、奥スコア 165..197、中央キューブ 200..240、手前スコア 243..275、手前トレイ 278..379、手前持ちキューブ 382..422（x 658..698）。間は全部 3。
Crawford: 1 行目 x 660.9..695.6、y 204.3..219.7、2 行目 x 664.4..691.6、y 220.3..235.7（中央の場合。キューブ 200..240 の内側）。手前持ちも同じ相対位置。cube-num は y 27.3..49.5（奥持ち、キューブ 18..58 の内側）。
トレイに 15 枚: 奥は板 y 65..139、枚数の字 141.5..158.6（トレイ 61..162 の内側）。手前は板 301..375、字 281.5..298.6（トレイ 278..379 の内側）。
`uv run pytest analyzer/test_pwa.py`: 31 passed。
