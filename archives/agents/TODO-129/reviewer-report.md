# TODO-129 reviewer の報告

対象: `git diff`（ブランチ claude/todo-129-no-summary、未コミット）

要修正: なし

## 検討

### 1. 終局の画面に、終局だと分かるものが何も残らない（境界線上。報告だけ）

- `analyzer/static/result.js:36-63`
- 実測: node で `game_over: true` の結果（`analysis.py:112` と同じく `probabilities`・`moves`・`cube` が null）を
  `BgResult.html` に渡すと、ダイスの有無によらず次の 1 行だけになる。

  ```
  <p class="note">gnubg 2手読み・勝率とエクイティはキューブなし。Position ID: <code>…</code></p>
  ```

- 終局の局面で消すのはユーザーが決めたことなので、消し方としては指示どおり。ただ、結果の画面は
  盤面図とこの注記だけになり、誰が勝ったか・終局していることは盤面図（上がりが 15 枚）からしか読めない。
  注記の「勝率とエクイティはキューブなし」も、どちらも出ていないので意味をなさない（前からある文言だが、
  今回これだけが残るので目立つ）。実害（利用者が壊れた画面と思うか）は未確認。

### 2. README の「下の注記」が何を指すか分からない

- `analyzer/README.md:93` 「終局しているときは、下の注記だけになる（TODO-129）」
- 注記（gnubg の手読み・Position ID の行）は、この文書のどこにも説明が無い（`rg -n '注記|手読み' analyzer/README.md`
  で 93 行目だけ）。「下の」も、この段落の直前に並べた項目を指すように読める。実装どおりなら
  「盤面図と、一番下の注記（gnubg の手読みの深さと Position ID）だけになる」のように中身を書いた方が誤読が無い。
- 同じ行の「下と同じことなので」の「下」は、文中では前に並べた棒グラフ・キューブ・表を指している（画面では下なので
  間違いではない）。好みの範囲。

## 問題なし（1 行ずつ）

- result.js: `summary` を参照していたのは消した 1 か所だけ。`esc` はほかで使っている。`speechText` は `summary` を使っておらず変わらない
- style.css: `.result .summary` の規則はほかで使われていない（`rg -n summary analyzer/static` で残るのは `<details>` の `summary` 要素と `.tips > summary` だけで、別物）
- tools/: `pi_ui_check.py`・`ui_snapshot.py` に `.summary` を探すところは無い。`check_pi.py` は API の `summary` を使うので影響なし
- test_pwa.py: 概要を戻すと `at[0] == 0` と `"手前が有利" not in html` の両方で落ちる（コードを読んで確認。壊して流すのは verifier の担当）。終局の html のテストは無いが、`let out = ""` は終局と共通なので同じ行で守られている
- 版: analyzer のコードの変更（画面の変更）で 0.72.0 → 0.73.0、`app.py` と `APP_VERSION` が一致。`rg '0\.72\.0'` で古い版の残りなし。CLAUDE.md の「バージョン」どおり
- コメント: 「なぜ」（下と同じことを言っていた）を書いている
- 範囲: 指示に無い変更は無い（TODO.md の更新は項目の決定とチェックのみ）

## 作り込みすぎ

作り込みすぎ: なし（Lean already. Ship.）
