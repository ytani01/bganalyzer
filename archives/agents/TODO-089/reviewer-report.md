# TODO-089 reviewer の報告

対象: `git diff main...claude/todo-089`（53e5fdb）。コードは直していない。

## 要修正

### analyzer/README.md:56 「黒の番なら白から見た n が 25−n」が、手前が暗い色のときに逆になる

- 何が問題か: README の 39 行目で、画面の「白」「黒」は駒の色の呼び方で、手前の駒が暗い方なら手前が「黒」になると決めている。
  実装（`board.js` の `number`）は内部の `"black"`（奥）の番で 25−n にする。手前が暗い方のとき、README のとおり読むと
  「黒（= 手前）の番で 25−n」になり、実装と逆になる。
- 根拠: `analyzer/README.md:39`、`analyzer/static/result.js:11`（`bottomColour === 0` で `white: "黒"`）、`analyzer/static/board.js` の `number`。
- 実害: 文書だけ。挙動には影響しない。「奥の人の番なら手前から見た n が 25−n」のように写真の向きで書けば色によらない
  （README 40 行目の「写真の向きそのものを言う所は手前のまま」の決まりにも合う）。

## 検討

なし。

## 好みの範囲

### analyzer/static/moves.js:42 と board.js の `number` が対になっている

- `moves.js` の `index = (n) => (side === "white" ? n - 1 : 24 - n)` は `number` の逆写像（24 通りとも逆になることを node で確かめた）。
  片方だけ変わるとずれるが、どちらも決まった式で、今は食い違いは無い。コメントで互いを指すかどうか程度。

## 観点ごと（問題なし）

- 手番に `state.onRoll` を使うこと: 問題なし。`update()` が毎回 `state.onRoll` を `BgCube.request(...).on_roll` に揃えるので、
  `state.onRoll` は解析に送る `on_roll` と常に同じ。サーバーは送られた `on_roll` をそのまま返し（`analysis.py:101`）、
  写真の解析でサーバーが `on_roll` を替えるのは `doubled` のとき（ダイス無し = 手が無い）だけ（`app.py:291-296`）。
  `resultFits` は `inputsKey` に `s.onRoll` を含むので、矢印（`moveToShow`）が出るときは `r.on_roll === s.onRoll`。
  結果の画面へは「解析する」からしか入れず（`resultStale` なら解析し直す、`app.js:876`）、popstate は戻るだけなので、
  結果の一覧（`r.on_roll`）と結果の盤（`s.onRoll`）が食い違ったまま見える経路は見つからなかった。
  - 補足（境界線上・報告だけ）: キューブを提示した局面（テイク／パス）では `state.onRoll` はダブルした側（受ける側ではない）で、
    盤の番号もダブルした側から見たものになる。手の一覧が無い局面なので棋譜とのずれは起きない。依頼文の「受ける側に替わる」は、
    コードを読む限り「ダブルした側（`other(cube.at)`）に替わる」。これで良いかは判断していない。実害は未確認（無いと見ている）
  - 補足（意図どおりと見ている）: 直す画面で「次に振る人」を切り替えると、編集中の盤の番号もその場で全部入れ替わる（TODO.md の「すべての盤で」の決めどおり）
- 番号の文字列やインデックスを別の所で使っていないか: 問題なし。`.num` は表示だけ（CSS の `style.css:179`）。番号をタップして空にする
  `hit-num` は `i`（`points[]` のインデックス）を渡しており、文字列は読まない（`board-view.js:98`）。パレットの `p.at` もインデックスのまま
  `BgBoard.set` / `countOf` に渡している。`sample.js:39` の `fixed_points` は `i + 1`（手前から見た番号）のままで、これは送るデータの形なので変えないのが正しい
- 版: 問題なし。analyzer 0.53.0 → 0.54.0（表示の変更なので機能の変更扱い）、`APP_VERSION` も 0.54.0、`sw.js` の CACHE も v58 → v59。古い版の文字列は残っていない（archives 以外を `rg`）
- README / 注記: 上の要修正の 1 件以外は問題なし。結果の画面の注記（`result.js:55`）は、結果が盤に合うときしか結果の画面に出ないので正しい
- テスト: 問題なし。`[1, 24, 24, 1, 19]` は、常に `i + 1`（→ `[1, 24, 1, 24, 6]`）、`25 - i` などの 1 ずれ、白黒の取り違えのどれでも落ちる
  （`uv run pytest analyzer/test_pwa.py -k board_model` は 1 passed）。ただし `board-view.js` と `app.js` が `number` を呼んでいることは
  テストしていない（描画のテストがもともと無い）。そちらはマージ後の「ローカル:」の確認で見る形
- コメント: 問題なし（`number` のコメントは向きの意味を書いている）
- 範囲: 問題なし（指示に無い変更は無い）
- 規約: 問題なし（`points[i]` の向きは変えていない）

## 作り込みすぎ

作り込みすぎ: なし（`number` は 1 行で、呼ぶ所が 2 つ。Lean already. Ship. net: -0 lines possible.）
