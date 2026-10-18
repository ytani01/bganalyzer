# TODO-144 レビュー（reviewer）

対象: `git diff main...HEAD`（claude/sheet-no-scroll。style.css の `.sheet` に `touch-action: none`、analyzer 0.79.1）

要修正: 0 件

## 検討

- `analyzer/static/style.css:292` / シートの上で始めたピンチズームとダブルタップのズームも効かなくなる /
  `touch-action: none` はパンだけでなくズームも止める（仕様）。`index.html:5` の viewport は
  `user-scalable=no` を付けておらず、ほかの場所ではズームできる。シートの文字を拡大して読みたい人は、
  シートの外からピンチすることになる。パンだけ止めてピンチを残すなら `touch-action: pinch-zoom`
  がある。実害は未確認（スマホでシートの上をピンチする人がいるか分からない）
- iOS の Safari で目的が果たせるか / 未確認 / `touch-action: none` は iOS 13 以降の Safari が
  対応している（それより前は `auto` と `manipulation` だけ）。手元に iOS の端末が無く実測していない。
  同じ指定を `.canvas-wrap` と `#photo-canvas`（style.css:182-183）で前から使っていて、四隅の画面で
  指で角を動かしても画面がスクロールしないのはこの指定のおかげ（corners-view.js の `pointerdown` の
  `preventDefault()` ではスクロールは止まらない）。利用者の端末で前から効いている根拠にはなる。
  最後の判断は TODO.md の「スマホ:」の行で

## 観点ごと（問題なし）

- タップ: 問題なし。モバイル表示の Chromium（412x700、`has_touch`）で `#sheet-cube` を出し、
  `.seg` のボタン・✕・`#cube-value`・`#cube-offered` を `tap()` すると、`touch-action: none` でも
  `auto` でも 4 つとも `click` が来て、チェックボックスも外れた（computed は `none` を確認）。
  `touch-action` はブラウザのパン・ズームだけを決め、タップの `click` は変えない。ダイスの目のボタン
  （`#die1`/`#die2 button`）とほかのプルダウンは同じ `<button>`・`<select>` なので代表で足りる。
  ネイティブのプルダウンの選択肢が開くところは headless では見えず未確認
- スクロールが止まるか（Android の Chrome）: 実測できなかった。CDP の
  `Input.synthesizeScrollGesture` が、シートの外でもスクロールしなかった（scrollY 500→500）ため、
  比べられていない。仕様上は Chrome で効く。`overscroll-behavior` は要らない: スクロールの
  コンテナでない要素には効かず、シートは中でスクロールしないので、パンを止める `touch-action` だけが効く
- 画面の低い端末: 変わらない。シートは `position: fixed` で `max-height`・`overflow` が無く、
  前から下の画面をスクロールしても動かないので、はみ出した分は前から見られない。412px 幅で
  キューブのシート（`#cube-side` を出した状態）の高さは 270px で、`--bar-h` を足した高さが
  画面より高くなるのは横向きの低い端末くらい（未確認、差分の前からの話）
- 版: 問題なし。analyzer/static を変える直しなので 0.79.0 → 0.79.1、`APP_VERSION` も同じ。
  0.79.0 が残るのは TODO.md の過去の確認の記録だけ
- コメント: なぜ（中でスクロールしないので、指の動きを下へ渡さない）を書いている。問題なし
- 範囲: 指示の外の変更なし
- 文書: analyzer/README.md:91-93 のシートの説明に、スクロールの挙動の記述は無く、直す所なし
- 作り込みすぎ: なし
