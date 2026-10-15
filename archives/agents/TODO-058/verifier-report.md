# TODO-058 確認報告（PI-041 の画面タイトル、Raspberry Pi）

実施: 2026-10-16、Pi 上。測定スクリプトは `archives/agents/TODO-058/measure.py`、出力は `archives/agents/TODO-058/measure-output.txt`。
スクリーンショットは `~/tmp/playwright-mcp/todo058-<幅>-<画面>.png`（8 枚）。

## 検証の結果

- `systemctl --user restart bganalyzer` のあと `/version`: `{"analyzer":"0.40.2","recognizer":"0.21.2","commit":"7baf398","samples":true}`（終了コード 0）。期待どおり。
- 測定スクリプトの終了コード: 0（390px・1000px の両方で 4 画面ずつ完走）。

## 測った値

期待どおりのものは 1 行にまとめる。

- 画面タイトル `#title`: 390px・1000px とも、写真の選択 → 四隅の調整 → 盤面の確認/修正 → 解析結果 の順で一致。
- 切れ: 8 画面すべて `scrollWidth == clientWidth`（例: 390px 盤面 189/189、1000px 解析結果 844/844）。切れていない。
- `.app-name` と `#hdr-version` の位置: 8 画面すべて同じ行（top は 8 と 9。差 1px で、判定の 2px 以内）。`#hdr-version` の bottom は `header .bar` の top より上（`verAboveBar: true`）。
- `#hdr-version`: 8 画面すべて「v0.40.2 · r0.21.2」。待たずに出た（2 秒待ちの再読は不要）。
- 横のはみ出し: `documentElement.scrollWidth` は幅と一致（390/390、1000/1000）。見えているヘッダーのボタンは右端を越えず（`headerRightOverflow: false`）。
- ボタンの右端（参考）: 390px では 盤面の画面の「解析する」が right 374、1000px では 984（画面幅 390／1000 の内側）。

食い違い: なし。

## スクリーンショットの目視

8 枚とも、ヘッダーの 1 行目にアプリ名と版、2 行目に画面タイトルと操作ボタンが出ていて、文字の欠けや重なりは見えない。1000px の 2 行目（工程表示）もタイトルと重ならない。デザインは評価していない。

## 確かめられなかったこと・判断が要る点

- 判断が要る点は無し。
- 実害は未確認。例えば iPhone の実機やスマホの見た目は、このヘッドレス Chromium では確かめていない（PI-041 の「スマホ」の項目は ai1 の担当）。
- 測ったのは Chromium の描画で、Safari の文字幅とは違うかもしれない。
- 「同じ行」は top の差 1px で判定した。`.app-name` と `#hdr-version` の文字の並びそのものは目視のみ。
- 文言の良し悪し、pytest、他の PI 項目は見ていない（指示どおり）。
- コードは変更していない。

## 追加の確認（コミット 43e4958、手順表示 `#steps` をタイトルと同じ語にした）

実施: 2026-10-16、Pi 上。`systemctl --user restart bganalyzer` のあと `/version` は `{"analyzer":"0.40.2","recognizer":"0.21.2","commit":"43e4958","samples":true}`（期待どおり）。
測定は `archives/agents/TODO-058/measure.py steps 600 1000 390`（終了コード 0）。出力は `archives/agents/TODO-058/measure-steps-output.txt`。
スクリーンショットは `~/tmp/playwright-mcp/todo058-steps-<幅>-<画面>.png`（600・1000 の 4 画面ずつ、390 は写真の選択のみ）。

### 測った値

- `#steps span` の文字列（600・1000 の 4 画面とも同じ）: 「1 写真の選択」「2 四隅の調整」「3 盤面の確認/修正」「4 解析結果」。期待どおり。
- `on` の付いた span（画面ごとに 1 つ）: 写真の選択 → 「1 写真の選択」、四隅 → 「2 四隅の調整」、盤面 → 「3 盤面の確認/修正」、解析結果 → 「4 解析結果」。期待どおり。
- 4 つが 1 行か: 600・1000 とも各 span の top の差は 0（tops 70.9 が 4 つ）。
- 右端と横のはみ出し: 600px は最も右の span の right が 434.9〜478.5（画面で変わる）、1000px は 434.9〜478.5。`beyondRight: false`、`docScrollW == innerW`（600/600、1000/1000）。はみ出しなし。
- 390px: `#steps` は `display: none`（navVisible false、span の top と right はすべて 0）。見えていないことを確かめた。期待どおり。
- ヘッダーの値（前回と比べる）: タイトル文字列・切れ（scrollWidth == clientWidth）・`.app-name` と版の同じ行・版「v0.40.2 · r0.21.2」・ボタンの位置は、1000px と 390px の前回の値と一致（例: 1000px 盤面のタイトル right 885.3、解析する right 984。390px 写真の選択の titleRect right 366）。600px は前回測っていないので今回の値だけ（タイトル scrollWidth == clientWidth、版は同じ行、はみ出しなし）。変わっていない。

食い違い: なし。

### スクリーンショットの目視

600px 4 枚と 1000px 4 枚、390px 1 枚を見た。文字が欠けたり重なったりしているものはない。「1 写真の選択」などの span も行内に収まっている。600px の 2 行目は「盤面を読み取る」ボタンと重ならない。デザインは評価していない。

### 確かめられなかったこと

- 実害は未確認。Safari など別のブラウザの文字幅では確かめていない。
- 判断が要る点は無し。

## 追加の確認（2）（コミット c5fb6c0、行頭のアイコンと `.app-name` を 16px の太字に）

実施: 2026-10-16、Pi 上。`systemctl --user restart bganalyzer` のあと `/version` は `{"analyzer":"0.40.2","recognizer":"0.21.2","commit":"c5fb6c0","samples":true}`（期待どおり）。
測定は `archives/agents/TODO-058/measure.py icon 390 1000`（終了コード 0）。出力は `archives/agents/TODO-058/measure-icon-output.txt`。
スクリーンショットは `~/tmp/playwright-mcp/todo058-icon-<幅>-<画面>.png`（390・1000 の 4 画面ずつ、計 8 枚）。

### 測った値

- `.app-icon`（8 画面とも同じ）: complete true、naturalWidth 150、表示 20×20px、left 16。`.app-name` より左（leftOfName true）。縦の中心の差 0.0px。期待どおり。
- `.app-name`: font-size 16px、font-weight 700（bold）。期待どおり。
- `.app-name` と `#hdr-version` の縦の中心の差: 0px。アイコン・名前・版は同じ行（sameLine true）。
- `#hdr-version`: 8 画面とも「v0.40.2 · r0.21.2」。scrollWidth 87 == clientWidth 87 で省略（…）なし。期待どおり。
- 前回の値との比較:
  - タイトル文字列とタイトルの幅（scrollWidth == clientWidth）: 390px は 350 / 141 / 189 / 234、1000px は 960 / 751 / 799 / 844。前回と一致。切れなし。
  - 手順表示（1000px）の最も右の right: 434.9 / 449.4 / 464 / 478.5。前回と一致。390px は非表示のまま。
  - はみ出し: docScrollW == innerW（390/390、1000/1000）、headerRightOverflow false。前回と一致。
  - 位置の変化（判断の要る変化ではないが、前回と違う）: タイトルの top が 34.1 → 38、ヘッダーのボタンの top が 27.4 → 31.3 に下がった。`.app-name` が 16px になったため行の高さが増えた。ボタンは右端を越えない。

食い違い: なし（位置が下がったのは上の表のとおりで、期待に反する値ではない）。

### スクリーンショットの目視

8 枚とも、行頭のアイコン（小さな盤のような絵）が欠けずに出ていて、「BG Analyzer」「v0.40.2 · r0.21.2」と同じ行に並ぶ。文字やボタンとの重なりは見えない。1000px の手順表示も重ならない。デザインは評価していない。

### 確かめられなかったこと

- 実害は未確認。Safari など別のブラウザでの見え方は確かめていない。
- アイコンの絵柄が意図どおりかは見ていない（読み込まれ、表示されたことだけを確かめた）。
- 判断が要る点は無し。
