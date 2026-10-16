# TODO-066 implementer の報告

## 変更点

- API
  - `analyzer/models.py:28-32` `AnalyzeRequest` に `match_length`（0 = マネー）・`score_white`・`score_black`・`crawford`
  - `analyzer/analysis.py:74-87` 検証（422）: 長さ 0〜64（gnubg の上限）、マネーではスコア 0・クロフォードなし、スコアは 0〜N−1、
    クロフォードは片方だけが N−1 のとき、クロフォードではキューブは中央の 1（`doubled` も不可）
  - `analyzer/analysis.py:99` 結果に `match`（`{"length", "score": {"white", "black"}, "crawford"}`、マネーは `null`）
  - `analyzer/analysis.py:115-121` engine には手番側のスコアを先にし、評価用のキューブ（数・持ち主）も一緒に渡す
  - `analyzer/analysis.py:167`・`188-193` `summary_ja` の先頭に `match_ja()`「7 ポイントマッチ 手前 3 対 奥 5（クロフォード）。」
  - `analyzer/app.py:72-75`・`127-129` `/analyze`、`171-174`・`192-194`・`252-254`・`292-293` `/analyze-photo` の Form と `_photo_result`
  - `analyzer/app.py:31` 版 0.48.0
- engine（`analyzer/engine.py`）
  - `:60-72` `_cube_infos`: マッチは `gnubg.cube_info(value, owner, 0, N, (手番, 相手), crawford, 0)` と相手側の分。
    **マネーも `cube_info(1, -1, 0, 0, (0, 0), 0, 0)` と全部書くようにした**（後述の不具合のため）
  - `:76-83` `evaluate`・`find_best_moves`・`_complete_moves` に渡す。`_complete_moves`（`:241`、`:262`）の相手側の評価も相手側のスコアで
  - `:116-139` `_cube_hint`: マッチは毎回 `new match N` → `set score A B` → `set crawford on|off`、マネーへ戻すときだけ `new session`
- PWA
  - `analyzer/static/index.html:40-48` ヘッダーの nav の上に 1 行（長さの select、手前・奥のスコア、クロフォードのチェック。スコアはマッチのときだけ、クロフォードは片方だけ N−1 のときだけ出す）
  - `analyzer/static/style.css:89-93` その行の見た目
  - `analyzer/static/cube.js:33-51` `fixMatch`（値を揃える）・`canCrawford`・`matchRequest`（API のフィールド）
  - `analyzer/static/app.js:29-31` localStorage `match` を JSON で読み出し（try/catch、`fixMatch` を通す）、`:67` state、`:86` `inputsKey` に入れる（変えると結果が古い扱い）、
    `:302-317` 描画、`:515-523` `setMatch`（端末に残し、解析結果の画面なら `analyze()`）、`:781` `/analyze-photo`、`:827-828` `/analyze`、`:1049-1055` イベント、`:14` 版 0.48.0
  - `analyzer/static/result.js:18-22` `matchText`、`:55` キューブの注記（マッチなら「キューブの判断はマッチのスコアで」）、`:100` 読み上げの最後に「7 ポイントマッチ 手前 3 対 奥 5です。」
- テスト: `analyzer/test_api.py:455-517`（4 本）、`analyzer/test_pwa.py:238-286`（3 本）
- 文書: `analyzer/README.md:128-130`・`154-161`・`193`、`docs/PI_CHECKS.md` に PI-048（次の番号を PI-049 に）

## 検証

- `uv run pytest analyzer/test_api.py analyzer/test_pwa.py -q` → 63 passed、終了コード 0
- `node --check` app.js・cube.js・result.js → OK
- ruff: 変える前と同じ 35 件（増やしていない）
- 壊すと落ちるか（それぞれ戻してから次へ）:
  1. engine に渡すスコアを逆順にする → 4 本落ちる
  2. マネーの cube info を `gnubg.cube_info()` に戻す → 2 本落ちる
  3. `new session` をやめる → `test_match_score_changes_the_answer` が落ちる
  4. `set crawford` を常に off にする → `test_no_double_in_the_crawford_game` が落ちる
- 手元の Playwright（/usr/bin/chromium、390x844、手で入力 → 7 ポイント 3-5 → 解析 → 結果の画面でマネーに戻す → 5 ポイント 4-0 クロフォード → 再読み込み）で一通り動き、
  再読み込み後も前の値が残る。ページのエラー 0。確認の担当の分の代わりではない

## 見つけて直した不具合

`gnubg.cube_info()` を引数なしで呼ぶと、helper の gnubg セッションの今のマッチを使う。`_cube_hint` がマッチを作った後のマネーの評価
（`evaluate`・最善手）がマッチのスコアで計算されていた（初期配置のエクイティが 0.068 → 0.351）。マネーの cube info を全部書いて直した。テスト 2 で捕まる。

## 判断が要る点

1. **マッチで「有利」の側と勝率が食い違って見える。** `favourite` はエクイティの符号で決めていて、マッチではマッチの勝率から出したエクイティになる。
   初期配置・3-5 で手前が振るとき「奥が有利: 勝率 47.5%」と、ゲームの勝率が低い側が「有利」になる（マネーは変わらない）。
   直すなら、`favourite` をゲームの勝率で決めるか、マッチでは文言を変えるか。今は手を付けていない
2. **`Optional double, take`** は今の `_cube_result` では `double: false`（「まだダブルしない」）になる。下調べのとおりマッチで出ることがある。どう読ませるか未決
3. スコアの書き方は依頼の例「3-5」ではなく「手前 3 対 奥 5」にした（どちらの点か分かるように）。読み上げは最後に入れた（最善手を先に聞けるように）
4. 評価にはマッチと一緒に今のキューブ（数・持ち主）も渡している（マッチではキューブの数でギャモンの価値が変わるため）。マネーは今までどおり 1・中央で、答えは変わらない
5. クロフォードのチェックは自動では入れない（片方が N−1 になっても既定はオフ = クロフォードの後）。初期値を入れたほうがよければ足す
6. マッチの長さの選択肢は 1〜25（API は 64 まで）

## 残る懸念

- `_cube_hint` は helper のセッションを書き換えるので、ほかに gnubg のセッションに頼る呼び出しを足すと同じ種類の不具合が出る（今は全部 cube info を明示している）
- PI-048 の期待値（2 手読みで `(4.1%)` / `(23.0%)`）は開発機で測った値

## 追記: reviewer の指摘を受けて直した点

1. 「有利」の側: マッチでは、このゲームの勝率（`win > 0.5`）で決める（`analysis.py` の `favourite`）。マネーはエクイティのまま。初期配置・3-5 の見出しは「手前が有利: 勝率 52.5%」になる
2. `/analyze-photo`: 解析だけ失敗したとき（`_run` の 422）は、盤面の誤りのときと同じく 200 で盤面を返し、`analysis: null`・`analysis_error`（理由）を付ける（`app.py` の `_photo_result`）。
   PWA は読み取りの後に alert を出す（クロフォードとキューブが原因なら日本語の文）。
   **既存のテスト `test_api_photo_dice_cancel_a_double_set_by_hand` の最後**（手でダブル＋手でダイス）も 422 からこの形に変わったので、テストを直した。PWA からは送らない組み合わせ
3. テスト: `test_api_moves_bearing_off_are_whole` に 7 ポイント 5-3 で `moves[0] == "3/off 1/off"` を足した。相手側のスコアを入れ替えないようにすると落ちる（確かめた）
4. 盤面の画面: クロフォードでキューブが片側のまま「解析する」と、送る前に日本語の alert で止める（`app.js` の `crawfordCube`・`CRAWFORD_CUBE`）。
   `Optional double` は `cube.optional` を足し、「ダブルしてもしなくてもよい」と出す（`summary_ja`・結果の画面・読み上げ）。
   `analyzer/README.md` の PWA の節にマッチの欄と読み上げのスコア、API の節に `optional`・`analysis_error`・マッチの `favourite` を書き足した
5. 作り込みすぎの 4 件: クロフォードの検証の `or doubled` を消した。評価に渡すのはキューブの数だけ（持ち主は渡さず、cube info の持ち主は -1）。
   `matchRequest` は値を付け替えるだけ（`fixMatch` は読み出しと `setMatch` で済ませる）。`MATCH_LENGTHS` を 1 行に縮めた

テストの結果:
- `uv run pytest analyzer/test_api.py analyzer/test_pwa.py -q` → 64 passed、終了コード 0
- 壊すと落ちるか: 相手側のスコアを入れ替えない → 上がりのテストが落ちる。`favourite` をエクイティに戻す → `test_match_score_changes_the_answer` が落ちる
- ruff は前と同じ 35 件。`node --check` OK
