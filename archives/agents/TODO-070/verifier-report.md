# TODO-070 verifier report（実害は未確認。境界線上の判断・原因の切り分けはしていない）

画面 390x844、Playwright（chromium）、各 1 回。サーバーは既に動いていた 127.0.0.1:8765（`/version` は analyzer 0.45.0 / recognizer 0.22.0。静的ファイルは作業ツリーから配信）。

## 1. pytest
`uv run pytest analyzer -q` -> 84 passed, 3 warnings (87.64s)、終了コード 0。

## 2. check_pwa.py（出力そのまま）
```
1 first: default size [2048, 1538]
  edit tools shown: True | corner tools hidden: True | recognize disabled: True | help: 写真の向きをボタンとスライダーで直し、写真の上を斜めにドラッ
  rect: [0.193, 0.303, 0.402, 0.552]
  after 確定: found size [428, 382] trimmed True err px: 21.8 | edit tools hidden: True
  history entry image: [428, 382, True]
2 first: found
  after 確定: found size [2048, 1538] trimmed False err px (of the photo's size): 150.9
```
終了コード 0、PAGE ERROR なし。
- 1: found / trimmed True / 21.8 px (<30) / 履歴の画像 428x382 = 確定後と同じ -> 一致
- 2: found / 150.9 px (<200) -> 一致

## 3. 追加の確認（archives/agents/TODO-070/verify_extra.py。写真は samples/collected-sj1vrx.jpg 2048x1538）
- 3a 一致: 矩形 [0.2,0.3,0.6,0.7]（元写真で 819x615 px）-> 「右に 90°」で state の rect は [0.3,0.2,0.7,0.6] に回る -> 確定後 [615, 819]（幅と高さが入れ替わる）、trimmed True。
- 3b 一致: 10° にすると `#edit-angle-text` = `10°`（state の angle も 10）。確定後 2048x1677（長辺 2048 以下）、trimmed False。左上・右下の画素は RGBA [0,0,0,255]（黒い隅あり）。回転前は 2048x1538 で、確定後の方が高さが大きい。
- 3c 一致: 回転と矩形のあと「やめる」-> 大きさ・四隅とも同じ、edit None、trimmed False。
- 3d 一致: 編集中に「戻る」-> step は photo、edit None。最近の写真から開き直すと edit None、`#edit-tools` 非表示、`#corner-tools` 表示、四隅 4 点。
- 3e 一致: 「もう一度検出」の find-corners 送信で、切り抜いていない写真は crop なし。切り抜いて確定した写真（819x615、履歴から開き直しても trimmed True）は `crop` = `0,0,819,615`。

3e の測り方の注意: `post_data` / `post_data_buffer` はこの環境で body が空で返ったため（長さ 0）、`FormData.prototype.append` を init script で包んで `crop` の値を拾った。ネットワーク上の実際の body は見ていない（`cornersForm()` が組んだ FormData の中身まで）。

## 4. スクリーンショット
- 編集中 (`o/1-cut.png`): 写真が欠けていない。点線の矩形と、左右 90°・スライダー・確定・やめるが出ている。写真の大半が黒いのは、サンプルの写真自体が盤の外を塗りつぶしてあるため（画面側の欠けではないように見える）。重なっているものなし。
- 確定後 (`o/2-cut-found.png`): 切り抜いた盤が枠いっぱいに出て、四隅の点 1〜4 が盤の遊戯面に載っている。欠け・余計な重なりなし。
- 保存先: /tmp/claude-649/-home-ytani-work-bganalyzer/fe7c8d28-b155-4a1e-897c-44e35611eb17/scratchpad/o/（ほか 3-turned.png、4-turned-found.png、5〜7 の png は撮ったが見ていない）

## 変更ファイル（git status）
TODO.md, analyzer/README.md, analyzer/app.py（__version__ 0.44.0 -> 0.45.0 のみ）, analyzer/static/{app.js, corners-view.js, history.js, index.html, photo.js, style.css, sw.js}, docs/PI_CHECKS.md、未追跡 archives/agents/TODO-070/（check_pwa.py, measure_cropped.py, reviewer-report.md、今回足した verify_extra.py, verifier-report.md）。
指示に無いファイルの変更は見当たらない（README.md の記述との照合までは見ていない）。

## 確かめなかったこと
- サーバーは今回の差分の Python（版の 1 行のみ）を読み込んだ状態か確認していない。`/version` の analyzer は 0.45.0 だった。
- 3e 以外の送信内容、4 のスクリーンショットのうち 3-turned / 4-turned-found / 5〜7。
