# TODO-176 reviewer の報告

対象: `git diff origin/main...HEAD`（d70336b・76a7161・09340ac）。

## 要修正

なし。

## 検討

- `analyzer/static/board-view.js:80`（変更なし。差分の外）/ 写真の側は `onPart` を渡さないので、
  `match` が残るのは `match.length` が 0 でないマッチのときだけ。そのときは viewBox の上に MATCH_H（26）の
  空の帯が残る（以前はそこに「◯ ポイントマッチ」が出ていた）。盤の側は `onPart` があるので常に帯がある。
  帯を残すことで盤の側と高さが揃うので、今回の目的には合っている。マネーゲームでは前から高さが違う
  （盤の側だけ帯がある）が、これは今回の差分で変わっていない。実害は未確認（画面は verifier が見る）。

## 好みの範囲

- `analyzer/README.md:102` の「元の写真の表示」に「写真だけを出す（番号や点数は出さない）」と書き足す
  ことはできる。いまの記述（同じ向き・同じポイントの並び・見るだけ）は差分のあとも正しいので、
  直さなくてよい。

## 見たこと（一致したもの）

- `photo` を渡す呼び出しは `analyzer/static/app.js:339` の `photo-svg` の 1 か所だけ（`rg -n "photo" analyzer/static`）。
  `onSelect`・`onPart` も渡していない。盤の側（`app.js:341`）と結果の画面は `photo` を渡さない。
- 盤の側の描き方: 消した `!photo` の判定（三角形・駒・バーの駒・felt の 2 枚・`if (photo) return`）は、
  `photo` が無いときは元から真／素通りだったので、盤の側の描き順・描くものは変わらない。
  `drawPoints`・`drawBar` の引数から `photo` を外したのも、中で他に使っていないことを読んで確かめた。
- viewBox・位置合わせ: viewBox と背景の rect は早く return する前に作るので、写真の側の viewBox は以前と同じ。
  `image` は以前と同じ `PLAY` の箱。写真の列合わせ（`photo.js` の補正）は画像の側でしているので影響なし。
- 版: `analyzer/app.py` 0.93.0 → 0.94.0、`APP_VERSION` も 0.94.0、`sw.js` の CACHE v60 → v61。
  表示の変更なので機能の変更として 0.x.0 を上げるのは CLAUDE.md の「バージョン」どおり。recognizer は変えていない。
- 冒頭コメント（09340ac）は新しい挙動（写真だけ）に合っている。
- `tools/ui_snapshot.py:84,347` は `photo-svg` の innerHTML のハッシュとクリックを見るだけで、中身の要素には依存しない。
  ハッシュは変わるが、版を比べる道具なので想定どおり。
- テスト: `board-view.js` のテストは無く、表示だけの変更なので足さなくてよい（確認は live_view の `- [ ] ローカル:` の行）。
- 範囲: 指示に無い変更は無い。TODO.md はチェックを入れただけ。

作り込みすぎ: なし（差分は削る方向で、分岐が 1 つにまとまった）。

---

# 追加の直し（353a28b）のレビュー

要修正: なし。検討: なし。

## 見たこと（一致したもの）

- 盤の側（board-svg）: 写真の分岐を `match`・viewBox・背景の rect より前へ移しただけ。`photo` を渡すのは
  `app.js:339` の photo-svg だけなので、盤の側の viewBox（`x0 y0 w h`）・背景・描き順は前と同じ。
- 写真の座標: viewBox は `PLAY.x PLAY.y PLAY.w PLAY.h`、`image` も同じ `x/y/width/height` なので、
  像は viewBox にぴったり収まり、切れない。像は `rectifiedPhoto`（`app.js:495-496`）が `PLAY.w*2 × PLAY.h*2` で
  作るので縦横比も PLAY と同じで、`preserveAspectRatio: "none"` でも歪まない。
- 前回の「検討」（マッチのとき写真の側に MATCH_H の空の帯が残る）は、写真の分岐が `match` の計算より前に
  return するようになったので、もう起きない。背景の rect も描かないが、`#photo-wrap` は `.board-wrap` の
  `background: var(--card)` を持つので見た目の地は同じ。
- 並び: `align-self: start` は `@media (min-width: 1000px)` の `.boards.two` の中だけ（`style.css:197`）。
  写真が無いとき・チェックを外したときは `#photo-wrap` が hidden で `.two` も外れる（`app.js:337-338`）ので効かない。
  スマホの縦（`style.css:332-336`、`.boards` が `display: contents`）と 700〜999px の 1 列のときも当たらない。
- index.html の `#photo-svg` の初期 viewBox（`0 0 660 440`）は描くたびに上書きされるので影響なし。
- 冒頭コメント（`board-view.js:5-6`「the photo in the playing area, none of the rest」）・README の「元の写真の表示」
  は差分のあとも正しい。版は同じ PR の 0.94.0 のままでよい（まだマージ前）。
- 範囲: 指示どおりの 2 ファイルだけ。

## 好みの範囲

- 広い画面では写真の側が PLAY だけに拡大されるので、写真の列と盤の側の列の横位置はもう揃わない
  （前のコメント「the same box as the board's, so it lines up」が言っていた揃い）。空白を消す利用者の指示の
  結果で、コメントも消してあるので直さなくてよい。実害は未確認（画面は verifier が見る）。

作り込みすぎ: なし（分岐の位置を移しただけで、コードは増えていない）。
