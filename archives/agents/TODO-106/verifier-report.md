# TODO-106 確認報告（verifier）

## 手順 1: speech_samples.js の 15 行

- 実行: `node archives/agents/TODO-106/speech_samples.js`、終了コード 0
- 期待の 15 行と `diff` で比べ、**一字一句一致**（diff 終了コード 0、行数 15）。
- 「白が有利です。」などの最後の形勢の文も含めて一致。

## 手順 2: pytest

- 実行: `uv run pytest analyzer/test_pwa.py -q -k "speech or result_html or match_in or names_follow or move"`
- 結果: 8 passed, 17 deselected, 終了コード 0。

## 手順 3: 壊すと落ちるか

作業前の `analyzer/static/result.js` を `/tmp/claude-649/-home-ytani-work-bganalyzer/8f84bca2-0c79-4ff5-8584-dc9dbe4ee578/scratchpad/result.js.orig` に退避し、各回の後に戻した。戻したあとの `git diff -- analyzer/static/result.js` は空（確認済み）。

(a) 112 行目 `c.optional ? ""` を `c.optional ? "x"` に変更:
- 1 failed, 7 passed。落ちたのは `test_match_in_the_result_words`。
- 出力（抜粋）:
  ```
  >       assert out["optional"][0].startswith("次は白の番です。") and "ダブル" not in out["optional"][0]   # TODO-106: not read out
  E       AssertionError: assert (False)
  E        +  where False = <built-in method startswith of str object at 0x7f791b1bd7f0>('次は白の番です。')
  E        +    where <built-in method startswith of str object at 0x7f791b1bd7f0> = 'x白がかなり有利です。ギャモン勝ちの見込みも十分あります。ピップ数では白が大きくリードしています。'.startswith
  ```
- 狙った分岐（optional の「読まない」）を見ている。

(b) 113 行目 `ギャモンを狙う方がよいです` を `まだダブルしません` に変更:
- 1 failed, 7 passed。落ちたのは `test_speech_reads_who_rolls_next_first`。
- 出力（抜粋）:
  ```
  E       AssertionError: assert False
  E        +  where False = <built-in method startswith of str object at 0x7f3127b2f330>('白はダブルせず、ギャモンを狙う方がよいです。')
  E        +    where <built-in method startswith of str object at 0x7f3127b2f330> = '白はダブルせず、まだダブルしません。白がかなり有利です。ギャモン勝ちの見込みも十分あります。ピップ数では白が大きくリードしています。'.startswith
  ```
- 狙った文言がテストで守られている。

注: 手順 3 の (a) はパイプ（`| tail`）越しに流したため pytest の終了コードは記録できなかった。出力の "1 failed" で落ちたことは確認した。(b) は終了コード 1 を記録。

## 変更ファイル

- 本確認の作業で変更したファイルは無い（`result.js` は一時変更後に戻し、差分ゼロ）。報告ファイルのみ新規作成。
- 作業前の `git status` はクリーンだった。

## 確かめられなかったこと・判断できないこと

- 手順 1 の `speech_samples.js` の入力がどの局面を表すかは確認していない（期待文との文字照合のみ）。
- テスト全体は流していない（指示どおり）。
- 境界線上の判断は無い。
