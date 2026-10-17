# TODO-111 レビュー（reviewer）

対象: `git show HEAD`（9b3e011）。実測は、このブランチを `uvicorn --port 8011` で起動し、Playwright（`/usr/bin/chromium`、ヘッドレス）で操作した。
使ったスクリプトは `/tmp/claude-649/-home-ytani-work-bganalyzer/8f84bca2-0c79-4ff5-8584-dc9dbe4ee578/scratchpad/m/`（probe.py〜probe5.py）。

## 要修正

### 1. `tools/pi_ui_check.py:97-100` speech の確認が最初の 1 文しか見ていない

- 問題: INIT の `play` の差し替えは `ended` を `setTimeout` で出すので、2 文目からはクリックのあと非同期に頼まれる。`page.click` の直後の
  `page.evaluate("window.__spoken")` では 1 文目しか入っていない。`%`・「勝率」・ピップの数・小数が無いかを確かめるのは 1 文目だけになる。
- 根拠（実測、3 回とも同じ）: evaluate したときは `len == 1`（`['白の 4 2 の最善手は、8から4、6から4です。']`）で、0.5 秒後には 2。
  全文は「…6から4です。ほぼ互角です。」。「ピップ数では…」のような文は後ろの方に来るので、そこに数字が入ってもこの確認では落ちない。
  変更の前は文を 1 つにまとめて渡していたので、全文を見ていた。`docs/raspi.md:130` には「1 文ずつ頼む分をつないだもの」を確かめると書いてあり、実際の動きと合わない。

### 2. `tools/ui_snapshot.py:36-39` INIT の差し替えを、pi_ui_check と揃えていない

- 問題: 同じ INIT を持つ 2 本のうち、`pi_ui_check.py` だけ `HTMLMediaElement.prototype.play` を差し替えた。`ui_snapshot.py` の manual の流れ（185 行の
  `r.click("#speak"); r.snap("read aloud")`）は、本物の `/speech` を叩いて Google に頼み、実際に音を鳴らす。
- 根拠（実測）: ui_snapshot の INIT のまま「読み上げ」を押すと、`__spoken` はクリックの直後も 3 秒後も `[]` で、ボタンは「止める」のまま。
  ボタンの表示と `spoken` が、Google の応答と音の長さで変わる。docstring の 24 行目「The recording is the same from run to run」が崩れる
  （何回か記録して食い違いが出るかまでは測っていない）。Google が断ったときは代わりにブラウザの音声合成に回るので、`spoken` に文が入る。

### 3. `README.md:44-48`・`README.md:82-89` 構成の図とファイルの表に `speech.py` が無い

- 問題: モジュール構成の mermaid 図（app.py のエンドポイントの一覧、`samplesapi`・`claudeapi` の箱）とファイルの表には、同じように
  ルーターを分けた `samples.py`・`claude_corners.py` が載っている。今回足した `speech.py`（`/speech`）はどちらにも無い。
- 根拠: `rg -n -e speech -e Google README.md` の結果は 0 件。`analyzer/README.md` には `GET /speech` の節を足してある。

## 検討

### 4. `analyzer/speech.py:22` 公開しているサーバーで、誰でも Google への中継に使える（境界線上なので報告だけ）

- 事実: `/speech` は環境変数の設定なしでいつも動く。`app.py:45` の CORS は `allow_origins=["*"]`。Funnel は URL を知っていれば誰でも届く
  （`docs/raspi.md:233`）。他所のページや第三者から 200 文字までの文を Pi の IP 経由で `translate_tts` に流せる。
- 影響（未確認）: 呼ばれる数が増えて Google が Pi の IP を止めると、持ち主の読み上げもブラウザの音声合成に回る。中継した文の出どころは Pi になる。
- 設計との差: CLAUDE.md の「外へ送るもの」のほかの 2 つは、`BG_SAMPLES_DIR`・`BG_CLAUDE` を「設定したサーバーだけ」と決めてある。
  `/speech` はその形になっていない（`/version` に出す仕組みも無い）。決めるのは管理者か利用者。

### 5. `analyzer/app.py:51-55` `/speech` の 502 の理由がログに出ない

- 事実: `log_http_error` が理由をログに出すのは 4xx だけ。`/speech` の 502（`translate_tts: HTTP Error 429` など）は、uvicorn のアクセスログに
  ステータスしか残らない。49 行目のコメントに「access log has the status but not why」とある。Google が断り始めたかを journal で追えない。
  `speech.py` で `log.warning` するか、ハンドラを 5xx にも広げるか。

### 6. `analyzer/static/app.js:1056` 読み上げの途中で「戻る」を押しても止まらない（前からの動き）

- 実測: 読み上げ中に `#back` を押すと、盤面の画面に移っても次の文の `/speech` が頼まれ続ける。ボタンの表示は「止める」のまま
  （盤面の画面ではボタンは隠れている）。前の版も `setResult` でしか `cancel` していなかったので、今回の差分で増えた問題ではない。
  結果の画面に戻ったときは「止める」で止まる。

### 7. `analyzer/static/app.js:148` 声が出ないまま終わる端末で、ボタンを押しても何も起きない

- 事実: ボタンを出す条件から `window.speechSynthesis` を外した。Google が断り、ブラウザにも日本語の声が無いと、何も鳴らずに表示だけ戻る。
- 実測: ヘッドレスの Chromium（声 0 個）で `/speech` を 502 にすると、`synthesis-failed` になって「読み上げ」に戻る。知らせは出ない。
  Google が動いていれば起きないので、扱いは管理者が決める。

## 確かめて問題が無かったもの

- 2 文目で失敗: 1 文目は `<audio>`、残りの「ほぼ互角です。」だけがブラウザの声に回り、終わると「読み上げ」に戻る（実測）
- 1 文目で失敗: 全文がブラウザの声に回る（実測）
- `play()` の reject と `onerror` が両方来るとき: ブラウザの声に回るのは 1 回だけ（`speaking !== audio` の確認が効く。実測）
- 止めるボタン → 「読み上げ」に戻る。最後まで読む → 戻る。2 回目の再生 → また鳴って「止める」になる。`pause()` で出る `AbortError` から
  ブラウザの声に回ることは無い（実測）
- ブラウザの声に回った直後の `speechSynthesis.speaking` は Chromium では `true` なので、そこで押しても止まる（実測。Safari は未確認）
- `sw.js:27`: スコープが `https://bg.tail5c266.ts.net/bg/` のとき、`/bg/speech?text=…` は除外され、`/speech`（ルート）と `/bg/app.js` は除外されない（node で確かめた）
- `test_speech_is_google_translate_voice`: `except OSError` を `ValueError` に、`max_length` を外す、`tl` を `en` にする、の 3 つの書き換えでどれも落ちる（実測）。JS の分け方と代わりの声への切り替えは、このテストでは守っていない（守っているのは 1. の pi_ui_check だけ）
- 版: analyzer 0.62.3 → 0.63.0（機能の追加）と `APP_VERSION` が揃っている。`CLAUDE.md`・`analyzer/README.md`・`docs/raspi.md` も直してある

## 作り込みすぎ

- `analyzer/static/app.js:1002`: delete: `speakWithBrowser` の `speakLabel(true)`。呼んでいるのは `fallback` だけで、そのときはもう `true`（969 行）になっている。代わりは要らない。重大度は好みの範囲。

net: -1 lines possible.
