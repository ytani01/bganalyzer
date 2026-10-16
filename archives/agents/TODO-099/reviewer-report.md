# TODO-099 レビュー（reviewer）

対象: `git diff main...claude/todo-099-impl`（d4c017e）。コードは読んだだけで、実行はしていない。

## 要修正

なし。

## 検討

### 1. `analyzer/static/result.js:23-26` / `matchText` がアプリから使われなくなった

- 何が: main では `matchText` の呼び出し元は `speechText`（result.js:132）だけだった（`git grep -n matchText main -- analyzer/static`）。
  今回それを消したので、`analyzer/static/` の中で呼ぶところが無くなり、残っているのは定義・export（result.js:162）と
  テスト（`test_pwa.py:351,358` の `text`、`test_pwa.py:372,377` の `match`）だけ。
- なぜ: TODO.md の背景に「画面の表示（`matchText`）はそのまま」とあるが、結果の画面のマッチの文は
  サーバーの `summary`（`analysis.py:209` 付近、result.js:37 で `r.summary` をそのまま出す）から来ていて、`matchText` ではない。
  TODO の前提が実際と違う。消すか残すか（`test_names_follow_the_colour` の名前の入れ替えの確認にだけ使われている）は判断が要る。
  実害は無い（使われないだけ）。

### 2. 盤の絵の新しい描画にテストが無い

- 何が: `drawMatch` と viewBox の伸び（マッチで 26 伸び、マネーゲームで変わらない）を確かめるテストが無い。
- なぜ: board-view.js の描画はもともと単体テストが無く（`test_pwa.py` は board.js の `_board_js` だけ）、
  今回もその作りに沿っている。代わりは verifier のブラウザでの実測と TODO.md の「ローカル:」の行。
  verifier への依頼に「マネーゲームで viewBox が `0 -38 660 518` のまま」「マッチで `0 -64 660 544`」を
  数値で読み出す確認が入っているかは見ておくとよい（値は board-view.js:19-22,61 から計算。未確認）。

### 3. `analyzer/test_pwa.py:359` / 読み上げのテストは、戻すと落ちるが範囲は狭い

- 戻すと落ちる: 消した行を戻すと `matchText` の「7 ポイントマッチ …」が speech に入るので、この assert は落ちる（コードから判断。実行はしていない）。
- 狭い点: 以前の `endswith(...)` は「読み上げの最後が何か」も見ていたが、今は「ポイントマッチ」が無いことだけ。
  スコアを別の言い方（「白 6 対 黒 5」など）で足し直しても通る。`"対" not in out["speech"]` を足すか、
  最後が形勢の文で終わることを見る assert があると強くなる。好みに近い。

## 作り込みすぎ

- `analyzer/static/result.js:23-26,162`: delete: `matchText` はアプリから呼ばれなくなった（上の 1）。テストの 2 か所と合わせて消せる。残す判断なら不要。
- `analyzer/static/board-view.js:208`: shrink: `cube = 30` は `drawCube` の `size = 30`（board-view.js:236）と同じ値の書き写し。片方だけ変えるとずれる。定数 1 つにまとめる程度。好みの範囲。
- `analyzer/static/board-view.js:60`: shrink: `scene.match && scene.match.length ? scene.match : null` は `scene.match?.length ? scene.match : null` で同じ。`draw` の呼び出し元は app.js:305-307 だけで、どれも `match` を渡すので `&&` の守りも本当は要らない。好みの範囲。

net: -6 lines possible（matchText を消す判断をした場合。テストの assert 2 行を含む）。

## 問題の無い観点（1 行ずつ）

- scene.match の受け渡し: app.js:295 の依存配列に `s.match` が入り、298 で scene に渡している。3 枚（photo-svg・board-svg・result-svg）とも同じ scene から描く。`s.match` は常に `BgCube.fixMatch` を通っている（app.js:30,534）。
- 履歴から開いたとき: 履歴は match を持たず（app.js:406-411）、写真を開くと `setResult(null)` するので、結果の盤が古いマッチを出すことは無い。
- white/black と手前/奥: `rowY("black")` が奥（ROW.top）、`rowY("white")` が手前で既存と同じ。板の色は `checkerFill(side)` で `bottomColour` の入れ替え（app.js:173-177）に従い、設定の `score-white` の見出し（`nm-white`）とも揃う。
- スコアの位置: home=right で x=54〜110、home=left で x=546〜602。キューブ（20〜50 / 606〜636）の内側、PIP の板（350〜446 / 210〜306）、真ん中のキューブ（313〜343）、トレイと重ならない（board-view.js の定数から計算）。
- タップの当たり判定: `levelAt` は `getScreenCTM` で座標を戻すので viewBox の y を変えても崩れない。`hit` / `hit-num` の矩形は y=0〜440 の中で、マッチの行（y=-64〜-38）とは重ならない。新しい要素は全部 `pointer-events: none`。
- tools: `ui_snapshot.py` は当たり判定の矩形の `bounding_box()` を使っていて viewBox の値に依存しない。
- 写真表示: `drawMatch` は `if (photo) return` より前なので photo-svg にもマッチの行が出て、横並びの 2 枚の高さが揃う（photo-svg にスコアだけ出て PIP は出ないのは見た目の判断で、評価しない）。台形補正（app.js:393 の `PLAY`）は viewBox と関係ない。
- 版: analyzer だけ 0.60.0 → 0.61.0（機能の追加なので minor）、`APP_VERSION` も同じ。recognizer は変えていない。sw.js はネットワーク優先で、最近の版上げでも `CACHE` は上げていない。
- README: analyzer/README.md:81,87 は実装と合う。他の文書（トップの README.md、docs/）に読み上げのスコアを書いた所は無い（`rg -e '対 黒' -e '最後にスコア' --glob '!archives/**'`）。README.md:179 はサーバーの `summary` の話で、変わっていないので正しい。
- 範囲: 指示に無い変更は無い。TODO.md のチェックは実装時点で入れる決まりどおり。`- [ ] ローカル:` の行もある。
- コメント: board-view.js:7-8,22,203-204 は「なぜ・どこに」を書いていて、TODO 番号の参照も規約どおり。
