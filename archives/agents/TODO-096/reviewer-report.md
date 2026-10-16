# TODO-096 reviewer の報告

対象: `git diff main -- analyzer/analysis.py analyzer/engine.py analyzer/static/result.js analyzer/test_api.py analyzer/test_pwa.py analyzer/README.md`
（TODO-095 の部分は見ていない）。要修正 0 件、検討 4 件、好みの範囲 1 件。

## 要修正

なし。

## 検討

1. **`analyzer/models.py:24` / コメントが古い。**
   `# The doubling cube (money game). Without dice, the answer has the cube decision.` のまま。
   ダイスがあっても（ダブルすべきだったときは）`cube` が返るようになったので食い違う。
   根拠: `analysis.py:121` の `elif cube_owner in (None, on_roll):` でダイスの有無を見なくなった。差分に入っていないファイル。

2. **`analyzer/README.md:73` / 画面の説明がダイスなしの場合しか書いていない。**
   「ダイスがなければ、中央なら次に振る人がダブルすべきかを…判定する」。間違いではないが、
   ダイスを入れたときに「キューブ（振る前）」が出ることはこの段落からは分からない（4. の段落と API の節には書いてある）。
   直すかは判断に任せる。

3. **`analyzer/README.md:185-187` / JSON の例に `rolled` が無い。**
   `_cube_result` は今は常に `rolled` を返す（`analysis.py:170`。ダイスなしでは `false`）。
   例と本文（182 行）で `rolled: true` だけ説明していて、ダイスなしでも `false` が入ることは書いていない。

4. **`analyzer/static/result.js:96-104` / 画面と読み上げで順番が逆。**
   画面はキューブ（振る前）→ 最善手（`result.js:44-46`、`test_pwa.py` で順序も確かめている）。
   読み上げは最善手 → 「振る前に白の人はダブルすべきでした。…」の順（`bestMove` を先に読む既存の方針、96 行のコメント）。
   TODO.md の仕様は「読み上げにも入れる」だけで順番は決めていないので、境界線上。報告だけ。

## 好みの範囲

- **`analyzer/analysis.py:197`** 概要の文が「…。振る前、白はダブルすべき、黒はパス」と読点が 2 つ続き、少し読みにくい
  （実測: `summary_ja` の末尾 `振る前、白はダブルすべき、黒はパス`）。「白は振る前にダブルすべきだった、黒はパス」なども考えられる。

## 問題なしの点（実測は `uv run python` で engine / analyze を直接呼んだ。plies=0、一部 2）

- 分岐: `doubled` とダイスの組は `analysis.py:78-79` で 422 になるので、`question: "take"` かつ `rolled: true` は起きない。result.js の `c.rolled` 分岐が take を潰す心配は無い。
- ダイスなし: `rolled: false`、フィルタは `dice is not None` のときだけ。既存の挙動のまま（`test_cube_decision_without_dice` 等 9 件通過）。
- 相手が持つ（`cube_value=2, cube_owner="black", dice=(3,1)`）: `cube` は `None`、`moves` あり。
- 自分が持つ・ダブルすべきでない（開始局面、`cube_owner="white"`、ダイスあり）: `None`。
- クロフォード + ダイス（7pt 5-6）: `cube` は `None`、`moves` あり。gnubg が "You cannot double." を端末に出すのは既存のダイスなしの場合と同じ経路（今回ダイスありでも出るようになっただけ）。
- クロフォード後 + ダイス: `Double, pass` で `rolled: true` が付いて出る（仕様どおり）。
- too_good / optional: `_cube_result` で `double` は `proper.startswith(("double","redouble"))` なので、"Too good…"・"Optional double…" は `double: false` になり、フィルタで落ちる（コードで確認。too_good の局面を 2 つ試したが gnubg は 0-ply で `Double, pass` と答え、too_good の実例は作れていない。実害は未確認）。
- engine の戻り値の変更: `rg -n "evaluate\(" analyzer` の呼び出し元は `analysis.py:127` だけ（`engine.py:77,261` は gnubg.evaluate）。漏れなし。
- `_cube_hint` を先に呼んでも手の評価は変わらない: マネー・7pt 5-6・7pt 3-5 × ダイス 3-1・6-5 を plies 2 で、cube あり／なしの `probs` と `moves` が一致。
- 時間: 開始局面・2 手読み・6-5 で、cube ありとなしの差は 0.01〜0.02 秒（開発機。Pi と 3 手読みは未確認）。
- 版: analyzer 0.58.0 → 0.59.0、`APP_VERSION` も同じ。CLAUDE.md の規則どおり。
- テストが壊すと落ちるか（コードを読んで判断。実際に壊しての確認はしていない）: `dice is None and` に戻す → `test_cube_decision_before_the_roll_with_dice` が落ちる。フィルタを消す → 同テストの開始局面 + 3-1 で `cube is None` が落ちる。`rolled` を常に false → 同テストが落ちる。result.js の `c.rolled` 分岐を消す → `test_result_html` の文言と見出しの assert が落ちる。
- 絞ったテスト: `pytest analyzer/test_api.py -k "cube or crawford"` 9 passed、`test_pwa.py -k "result_html or speech"` 2 passed。
- コメントは「なぜ」（TODO-096 の参照つき）。範囲外の変更なし。

## 作り込みすぎ

- `analysis.py:153`: yagni: `rolled: bool = False` の既定値。呼び出し元は 1 か所で常に渡す。既定値を外す。
- `result.js:70`: shrink: 見出しを三項で丸ごと 2 通り書いている。`` `<h2>キューブ${c.rolled ? "（振る前）" : ""}</h2>` ``。

net: -0 lines possible（重複が減るだけ）。
