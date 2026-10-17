# TODO-132 確認報告（verifier）

対象: 作業ツリーの未コミット差分（`git diff main`）。コードは直していない。

## 1. `uv run pytest -q analyzer/test_pwa.py`

- 結果: 26 passed, 1 warning（終了コード 0）
- 警告は fastapi/testclient の httpx 非推奨で、今回の変更とは無関係。

## 2. 壊すと落ちるか（kana() の `DIGIT[n % 10]` を `n % 10` に変更）

- 変更箇所: `analyzer/static/result.js` の kana() の一の位の `DIGIT[n % 10]` を `n % 10` に置き換えた（バックアップから戻し、`cmp` で元と一致を確認）。
- 結果: 3 failed, 23 passed。終了コードは取得できなかった（`EXIT=` が空。落ちた件数は出力どおり）。
- 落ちたテスト（出力を引用）:
  - `test_result_words`: `AssertionError: assert 'バー...`
  - `test_speech_reads_who_rolls_next_first`（test_pwa.py:123）:
    `'白の さん いち の最善手は、バーからにじゅうにでヒット、じゅう2でヒット、…'` の `startswith` 失敗。実際の出力に `にじゅう2でヒット`、`じゅう3からはちへに枚` と数字が残っている。
  - `test_result_html`（test_pwa.py:163）: 同様に `バーからにじゅうにでヒット、じゅう3からはちへに枚` の箇所で失敗。
- 判断: 狙った分岐（一の位の読み替え）だけが落ちている。テストは壊れた箇所を見ている。
- 戻したあとの `git diff main --stat`: `analyzer/static/result.js | 15 +++++++++++----`（11 挿入・4 削除）。指示どおり 15 行前後のまま。

## 3. node で値を読み出して確かめる

`R = require(".../analyzer/static/result.js")` で読み込んだ（test_pwa.py の `_result_js` と同じ読み込み方）。

| 呼び出し | 戻り値 |
|---|---|
| `R.moveToSpeech("24/18 8/2(2) 7/off")` | `"にじゅうよんからじゅうはち、はちからにへに枚、ななから上がり"` |
| 数字 `[0-9]` が残るか | 残らない（`digitsLeft: false`） |
| 「なな」を含むか | 含む（`hasNana: true`） |
| 「よん」を含むか | 含む（`hasYon: true`） |
| `R.moveToSpeech("bar/22* 13/8(2) 6/off")` | `"バーからにじゅうにでヒット、じゅうさんからはちへに枚、ろくから上がり"` |
| `R.html(...)` の最善手の見出し（ダイス 4-7、手 `24/18 8/2(2) 7/off`） | `最善手（白・ダイス 4-7）</h2><ol class="moves"><li data-k="0" class="on">24/18 8/2(2) 7/off<span>エクイティ 0.500</span></li></ol>…` |
| 画面に `24/18` が残るか | 残る（`htmlHas2418: true`）。ダイス `4-7` も数字のまま（`digitDice: true`） |

- 読み上げ（moveToSpeech）は数字を残さず、画面（html）は数字のまま。指示どおり。
- 文の並びに注意: 「へに枚」は枚数 2 を「に」で読む形（テストもこの形を期待している）。指示の範囲どおりで、問題とはしない。

## 変更ファイルと範囲

`git diff main --stat`:

- `TODO.md` 2 行
- `analyzer/app.py` 2 行
- `analyzer/static/app.js` 2 行
- `analyzer/static/result.js` 15 行
- `analyzer/test_pwa.py` 12 行
- 未追跡: `archives/agents/TODO-132/`（reviewer-report.md が既にある）

analyzer/app.py と analyzer/static/app.js は、ここで読んでいない（指示の範囲外）。`app.py` と `app.js` の 2 行ずつの変更は、版の上げ（`APP_VERSION` と `__version__`）と推定するが、内容は確かめていない。

## 確かめられなかったこと・判断が要る点

- 音声の読み上げ（実際の声）は見ていない（指示により対象外）。
- 他のテストファイルは流していない（指示により対象外）。
- 終了コードが取れなかったのは、壊した状態での pytest 実行だけ（落ちた件数と出力は残っている）。もう一度流すなら、戻した後の `uv run pytest -q analyzer/test_pwa.py` が終了コード 0 であることは 1 で確認済み。
- 手順の途中で、自分が起こした `cat`（stdin を読んで止まったもの）を 1 つ止めた。他の古い `cat` プロセス（PID 2730, 2731, 135207, 135208）は触っていない。
