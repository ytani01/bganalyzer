# implementer-report (TODO-123)

## 変えた点
- analyzer/static/index.html: `#edit-start` を `#turn-tools` の「右に 90°」の右へ。`#find-again`・`#claude-corners` を `#corner-reset` の行（`.row.wrap` に変更）へ。元の 3 ボタンの行は消し、`#claude-note` だけの `.row` を残した。
- analyzer/static/style.css:108 付近: `#match-score` を `display: contents` に。白・黒の select とクロフォードが `.opt`（flex-wrap）の子として並び、収まらないとき最後のクロフォードから次の行へ回る。`[hidden]` の規則はそのまま効く。
- analyzer/app.py:33 `__version__`、analyzer/static/app.js:14 `APP_VERSION` を 0.69.1 に（この 2 行だけ）。
- analyzer/README.md:45 の並びの説明。

## 検証
- `uv run pytest analyzer/test_pwa.py analyzer/test_api.py`: 74 passed。

## 残る懸念
- 390px で 1 行に収まるか、クロフォードだけが次の行に回るかは未測定（画面の確認の担当へ）。ラベル幅 6.5em + select 3 つで足りない場合、白・黒の select が先に折り返す可能性がある。
- 編集中は `#turn-tools` ごと「画像を編集」も隠れる（指示どおり）。

## 追記（確認で見つかった 2 か所の修正）
- ボタン名を「やり直す」「再検出」「Claude で検出」に変更: analyzer/static/index.html:94-96、analyzer/README.md、docs/corners.md、docs/raspi.md:161、recognizer/README.md:242。docs/raspi.md:214 の「下の「Claude に選ばせる」」は節の見出し（「Claude に四隅を選ばせる」）を指すので変えていない。
- ゲームの行: analyzer/static/style.css の `#match { gap }`、`#match .opt-label { width: auto }`、`#match-length { width: 8em }`、`#crawford-opt { flex-basis: 100% }`（クロフォードは常に次の行）。
- 幅を詰めるため、長さの select の文言を「N ポイントマッチ」「アンリミテッド」から「N ポイント」「マネー」に変えた（analyzer/static/app.js:1222）。8em だと「25 ポイント」が収まる見込みだが、実際の文字の切れ方は目視していない。
- 実測（check_ui.py、幅 390 / clientWidth 375）: 回転の行 SAME ROW、四隅の行（Claude 表示時も）SAME ROW。長さ・白・黒は四隅の画面（top 671.8）・盤面の画面（981.5）とも SAME ROW。クロフォードだけが次の行。scrollWidth 375。
- pytest（test_pwa・test_api）: 74 passed（8em にする前の 8.5em で実行。以降は style.css の数値のみ変更）。サーバーは PID で停止済み。

## 追記 2（ユーザーの決定: 長さの文言）
- 長さの select の文言を「N ポイント」「アンリミテッド」にした（analyzer/static/app.js:1222。「マネー」は戻した）。
- 幅は固定をやめ `#match-length { field-sizing: content }`（選んだ文字の幅に合わせる）と、`#match { gap: 4px }`（analyzer/static/style.css）。Chromium 以外で `field-sizing` が効かないときは、いちばん長い文言の幅になり、盤面の画面で「N ポイント」＋点数が収まらず黒の select が折り返す可能性がある（未確認）。
- 実測（幅 390、canvas で文字幅を測り select の clientWidth と比べた。文字幅 + 余白と矢印 32px で、切れない）:
  - アンリミテッド: w 143 / 文字 112。点数は隠れる。
  - 25 ポイント: w 117 / 文字 85。3 ポイント: w 108 / 文字 76。
  - 長さ・白・黒は四隅の画面（top 672）・盤面の画面（981）とも同じ行。クロフォードだけ次の行。scrollWidth 375。
- pytest（test_pwa・test_api）: 最終の変更後に 74 passed（下の結果参照）。サーバーは PID で停止済み。
