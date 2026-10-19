# TODO-171 reviewer の報告（2 回目）

対象: 前回のレビューの後のコミット `0f1112a`（`git show 0f1112a`）。前回の指摘が直ったかだけを見た。
テストは足した 2 つだけを流し、壊して落ちるかも確かめた（下記。確かめたあと元に戻し、`git status` が空なのを見た）。

## 要修正

なし

## 検討

なし

## 好みの範囲

### 1. `analyzer/test_pwa.py:1140` 置き場のタップは `bottomColour: 0` の 1 通りしか試していない

置き場のタップで送る色が `String(state.bottomColour)` であることを、`bottomColour: 0` → `"0"` の 1 件で見ている。`colourPick: "0"` と書き間違えても落ちない（読んで確かめた。壊して流してはいない）。`bottomColour: 1` の行を 1 つ足せば押さえられる。実害は未確認。

## 前回の指摘

- 1（README の古い記述）: 直っている。`analyzer/README.md:63`・`:74` が実装と合う。ほかに古い記述は `rg '端末に覚え'` で見つからなかった
- 2（手で盤面を作るときの色）: ユーザーが決めたとおり、文書（`:74`）を今の実装に合わせてある
- 3（置き場のタップ）: 直っている（`app.js:353`）。ほかの 4 つの経路は変わっていない。新しい写真は `:686` で `"auto"`、履歴の写真は `kept.colourPick`、PIP のタップは `:357`、手で盤面を作るときは `colourPick` を使わない。置き場をタップした写真を履歴から開き直すと、残した色（`:512`）で読むようになるが、ユーザーが決めたことに沿っている
- 4（テスト）: 3 つとも押さえている。壊して流した結果:
  - `sides = ("right",)` にする → `test_bottom_colour_is_guessed_from_the_pips` が落ちる
  - `guess_bottom` の既定を `default=0` にする → 同じテストが落ちる（`_finish` は `board.py:348` で既定のまま呼ぶ）
  - PIP のタップから `colourPick` を消す → `test_tapping_the_board_fixes_the_colour_sent` が落ちる
  - 置き場のタップから `colourPick` を消す → 同じテストが落ちる
- 5（`info.get`）: 直っている（`app.py:336`・`:452`）。差し替えるテストの側で `bottom_colour` と `colour_guess` を入れてある
- `pips()` の重複: 消えて `Position.pips()` の合計になっている（`board.py:110`）

## 作り込みすぎ

なし
