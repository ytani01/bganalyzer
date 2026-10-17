# TODO-111 確認の報告

対象: ブランチ claude/todo-111-google-tts、HEAD 8c8bfad。`git status` は確認の前後とも空（コードは変更していない）。

## 手順 1: tools/pi_ui_check.py speech（8001 番）

- 実行: `BG_CDP=http://127.0.0.1:9222 BG_URL=http://127.0.0.1:8001/ uv run -q --no-project --with playwright python tools/pi_ui_check.py speech`
- 終了コード 0。
- 出力:
  ```
  version: {'analyzer': '0.63.0', 'recognizer': '0.23.2', 'commit': '8c8bfad', 'samples': False, 'claude': False}
  OK   speech: spoken=['白の 4 2 の最善手は、8から4、6から4です。', 'ほぼ互角です。'] alerts=[]
  ```
- 文が 2 つ。期待（2 文以上）と一致。
- 注: この確認の INIT は `HTMLMediaElement.prototype.play` を差し替えて、再生の代わりに文を記録する。/speech の通信そのものは見ていない。通信は手順 2 で見た。

## 手順 2: 本物の再生（新しいページ 412×915、live_view のブラウザ）

スクリプトは作業場所の外（scratchpad）に置いた。`tools/pi_ui_check.py` の `read_photo` と `show_outcome` を import して使い、INIT は通していない。

- 経過: 8.67 秒（「読み上げ」を押してから aria-pressed が "false" に戻るまで）
- 応答（`/speech` の応答は 2 件）:

  | 応答の時刻 | status | content-type | text |
  |---|---|---|---|
  | 0.33 秒 | 200 | audio/mpeg | 白の 4 2 の最善手は、8から4、6から4です。 |
  | 6.92 秒 | 200 | audio/mpeg | ほぼ互角です。 |

- 戻った後のボタン: aria-pressed="false"、表示は「読み上げ」。alert は無し。
- 2 件目の要求は 1 件目の再生が終わるころ（約 6.9 秒）に出ており、順に再生されている。期待と一致。
- 応答の時刻は応答ヘッダーが届いた時点。再生の終わった時刻ではない。

## 手順 3: /speech を 502 にして、ブラウザの音声合成へ回す

- `page.route("**/speech?**")` で 502 を返し、`speechSynthesis.speak` を差し替えた。
- 差し替えの側で、`speak` に渡された `u.onend` を 300 ms 後に呼ぶようにした。手順の文面には無いが、これが無いと、ブラウザが読み終えた合図が来ず、ボタンが戻らない。ブラウザの動きに合わせた補いで、判定は変えていない。
- 経過: 0.36 秒。aria-pressed="false"、表示は「読み上げ」。
- `/speech` の応答: 1 件（502、文は 1 文目だけ）。2 件目の要求は出なかった。
- `speak` の呼び出し: 1 回。渡された文は `白の 4 2 の最善手は、8から4、6から4です。ほぼ互角です。`（lang ja-JP）。全部の文をつないだものと一致。
- alert は無し。

期待（speak に 1 回、全部の文をつないだ文、ボタンが戻る）と一致。

## 食い違い

なし。

## 確かめられなかったこと・判断が要ること

- 実際の音が出たかは確かめていない。再生の長さは、2 件目の要求が約 6.9 秒後に出たことからの推定。
- 手順 1 は再生を差し替えているので、手順 2 の結果で補った。
- 8001 番のサーバーは止めた（uv の PID 897178、子の uvicorn の PID 897183。どちらも終了を確かめた）。8000 番は 200 のまま。live_view の窓は閉じず、確認用に開いたページだけを閉じた。
- 境界線上の判断は無し。
