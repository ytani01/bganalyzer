# TODO-134 レビュー（reviewer）

対象: `git diff main`（未コミット）。要修正 0 件、検討 4 件、好みの範囲 1 件。

## 要修正

なし。

## 検討

1. **analyzer/test_api.py:265-293 / analyzer/app.py:168** — `side` は送らず `fixed` か `crop` を送ったときに `find_corners_any` へ回さない分岐が、テストで守られていない。
   根拠（実測）: 写しの上で `if f is None and c is None:` を `if True:`（fixed・crop を無視して自動判定に回す）に変えても、`test_api_find_corners` は通った。photo2 は通常の向きで正しく見つかるので、fixed[0] も四隅 4 つを固定した場合も、無視されたときと答えが同じになるため。
   `if False:` にした場合（自動判定を消す）は `test_api_find_corners_finds_the_side` が落ちる。WEAK を 0 にした場合、最後の `corners` の段階を送らない場合も落ちる。
2. **analyzer/README.md:228** — 「`corners` の段階は答えだけを最後に送る」は実際と違う。通常の向きの点数が低くても、`C.find_corners(img, progress)` は通常の向きの四隅で `corners` の段階を先に送る（recognizer/corners.py:390-391）。抑えているのは右・左の探索の `corners` だけ。side.py の docstring（「the searches tried again ...」）は合っている。
   PWA の表示（scan.js は段階ごとに最後に届いたものを描く）では、右・左の探索の段階を描いている間も通常の向きの緑の枠が残り、右・左が勝てば最後に差し替わる。通常の向きが勝てば、その枠がそのまま残る。表示が壊れるわけではないので、文書を合わせるか、通常の向きの `corners` も抑えて最後に勝ったものだけ送るかは判断待ち（実害は未確認）。
3. **analyzer/static/app.js:802** — 「利用者がチェックを変えたあとは切り替えない」に抜けが 1 つある。最初の探索中に、撮った位置を一度も選んでいない端末（sideFrom が ""）でチェックを入れると、`cornersAgain` は `was === sideSent()`（どちらも null）で何もせずに戻る。そのため最初の探索（switchSide=true）は止まらず、答えが横向きなら、聞いている最中の撮った位置をサーバーの答えで埋める（コードを読んだだけ。実際には動かしていない）。境界線上の判断なので報告だけにする。
4. **recognizer/side.py:159-176** — 通常の向きの点数が WEAK 未満か、何も見つからない写真（盤の無い写真、外れたスクリーンショット）では、探索が 3 回になる。Pi での待ち時間は測っていない（未確認）。確かめるならローカルの確認の行で。

## 好みの範囲

- **recognizer/side.py:174** — `if progress and best[2] and best[1]:` の `and best[1]` は外せる。best[2] が入るのは、右・左の点数が通常の向きを上回ったときだけ。点数は -1 以上で、同点のときは先にあるものが残るので、q が None（点数 -1）の向きは勝てない。

## 問題なし（1 行ずつ）

- しきい値の比較（`>= WEAK` なら通常の向きで返す）、None は -1 として扱う、`_view` が None でも -1: 意図どおり。
- `max(..., key=...)` は同点なら先のものを返すので、通常 > 右 > 左 の順で残る。前を優先する並びとして筋が通っている。
- `_score` は全ての向きを同じ RW×RH の真上からの図で採点していて、向き同士の比較が公平。`np.float64(q) * s` は crop が無いときの `find_corners` の縮小と同じ。
- app.py: side を送ったときは `side` に送った値を返し、corners が None でも同じ。fixed・crop のときは null。stream と非 stream で同じ dict を返している。
- PWA: 切り替えるのは `startPhoto` の最初の検出（`guessCorners(file, true)`）だけで、`cornersAgain` の `guessCorners(file)` では切り替えない。`keep()` を通さないので localStorage は変わらず、`historyRecord` で写真の記録には残る。以後は `sideSent()` を通して `/find-corners` の作り直しと `/analyze-photo`（app.js:917）に向きが渡る。cornersMoved のとき・別の写真に移ったときは切り替えない。古いサーバーで `data.side` が無ければ null。
- trimmed の写真（crop を送る）では自動判定しない。新しい写真は trimmed にならないので、README の「チェックが入っていない新しい写真」と合っている。
- 版: recognizer 0.24.0 → 0.25.0、analyzer 0.73.2 → 0.74.0、`APP_VERSION` も 0.74.0。機能の追加なのでマイナーを上げるのが CLAUDE.md の「バージョン」どおり。
- 文書: analyzer/README.md・recognizer/README.md・TODO.md に反映済み。TODO.md の冒頭の「何も見つけられなかったら…順に試す」は、着手時に決めたことの行で上書きしてある。古いまま残っている記述はほかに見つからない（`rg "TODO-134|find_corners_any|WEAK"`）。
- コメントは WEAK の値の根拠（photo5 0.46 / 1.1、正面 1.0 前後）と、なぜ切り替えるのかを書いている。
- 範囲: 指示に無い変更は無い。

## 作り込みすぎ

- recognizer/side.py:L174: delete: `and best[1]`（上の好みの範囲と同じ）。外すだけ。
- それ以外は無い。`_score` はほかに置き換えられる関数が無く（`C.find_corners` は点数を返さない）、`best` のタプルと `max` も短い。

net: -1 lines possible（実際は 1 つの条件を外すだけ）。

## 測ったこと

- `uv run pytest analyzer/test_side.py -k find_corners`: 2 件通過。`analyzer/test_api.py -k test_api_find_corners`: 1 件通過。
- 写し（scratchpad）で 1 か所ずつ壊して流した結果: WEAK=0 → 落ちる / 自動判定の分岐を消す → 落ちる / 最後の corners の段階を消す → 落ちる / fixed・crop を無視する → **通る** / WEAK=99（いつも右・左も試す）→ 通る（photo2 では通常の向きが勝つので、こうなるのが正しい）。
