# TODO-090 レビュー（reviewer）

対象: worktree `bganalyzer-090` の `git diff`（未コミット）。`uv run pytest analyzer/test_pwa.py` は 24 passed。
測るのに使ったスクリプトは scratchpad に置いた（リポジトリには入れていない）。

## 要修正

なし。

## 検討

### analyzer/test_pwa.py:129 — 手前（white）のバーのピップが試されていない

- 問題: `test_pips` でバーに置くのは奥（black）の駒だけ。`pips` の初期値を
  `let white = 0, black = 25 * b.bar_black` にして手前のバーを数えなくしても、テストは通る。
- 根拠（実測）: board.js のコピーを書き換えてテストと同じ式を node で流した。

  | 書き換え | 結果 |
  |---|---|
  | バーを 24 にする（両方） | 落ちる（black 191） |
  | 奥のバーを数えない | 落ちる（black 167） |
  | **手前のバーを数えない** | **通る** |
  | 奥を `25 - i` にする | 落ちる |
  | 手前を `i` にする | 落ちる |

- 手前の駒もバーに 1 つ置けば（例: `B.set(..., "bar", "white", 1)` を足して white 168 を期待する）落ちるようになる。

## 好みの範囲

- `analyzer/static/board-view.js:187` のコメント「between the tray and the cube in the middle」は、
  キューブが真ん中にあるときの手前の行のことだけ。奥の行や、キューブを誰かが持っているときは、札の隣にキューブは無い。

## 問題が無かったもの

- pips の数え方: `recognizer/position.py` の `Position.pips()`（API の `pips` の元）と同じ式。ランダムな盤 200 個（両方のバーに駒がある盤 22 個を含む）で、`BgBoard.pips` と食い違いは 0 件。
- 札と他のものの重なり（board-view.js を node で描いて座標を出した）:
  - 真ん中のキューブ（x 313–343）: 札は home=right で x 350–446、home=left で x 210–306。どちらも 7 px あく。
  - 持っている人の側のキューブは x 20–50 か 606–636 で、札から 300 px 離れている。
  - トレイ: home=right で x 450–636、home=left で x 20–206。上がった駒の数の文字（15 個のとき中心 x 470 / 186）はトレイの中で、札とは重ならない。
  - 「off」への矢印: home 2 通り × 手番 2 通り × 出るポイント 6 つ × 段 0–4 の全部で、影の線幅（8）と矢じりを入れても札と重ならない（いちばん近くて 6.8 px）。
- result.js の並べ替え: 元の版と新しい版の `html` を 6 つの場合で出し、h2 を p に読み替えたうえで部品ごとに比べた（チェッカーの手、手が無い（`moves: []`）、キューブ、マッチのキューブ、moves と cube が無い、game_over）。どれも部品は同じで、違うのは並び順だけ。game_over は概要の文と注記だけで、前と同じ。
- h2 に頼っているもの: `rg -n "h2" analyzer/static tools analyzer/test_*.py` で、概要の h2 を見ているコードは無い。`.result h2` の CSS は「最善手」と「キューブ」の見出しにまだ使われている。app.js は `BgResult.html` を innerHTML に入れるだけ（app.js:353）。
- 「バー」の文字を消した影響: `.label` の CSS は消してあり、ほかに `class: "label"` を使う所は無い。文書や tools/ にも盤の「バー」の文字の説明は無い。stackY のコメントも直してある。tools/ui_snapshot.py:122 のコメント「the bar's stacks start by its middle」は BAR_GAP の話で、今のままで合っている。
- テストの強さ（result.js）: テーブルを棒グラフの直後に戻す、概要を h2 に戻す、キューブのときテーブルを出さない、の 3 つはどれも落ちる（実測）。
- 版: analyzer 0.55.0 → 0.56.0（表示の変更なので minor）、`APP_VERSION` も同じ。recognizer は変わっていない。
- 文書: analyzer/README.md の 70 行目と 81 行目は新しい挙動と合っている。README.md:85 の「勝率・ギャモン率・ピップ・最善手を表示」は並びを書いていないので、そのままで食い違わない。
- 範囲: 差分は依頼の 4 点と TODO.md だけ。
- board-view.js の描画には自動テストが無いが、前からそうなっている（ほかの draw 関数も同じ）。画面の確認は verifier の担当。
- `sw.js` の `CACHE` は上げていない。上げる決まりは書かれておらず（TODO-092 でも上げていない）、取りに行くのはネットワークが先なので、実害は未確認。

## 作り込みすぎ

作り込みすぎ: なし（Lean already. Ship.）
