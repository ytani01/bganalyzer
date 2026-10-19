# TODO-157 確認報告（PR #467）

## 食い違い
- **依頼文のブランチ名 `claude/cube-colour` は PR #467 の head ではなかった。** そのブランチは origin/main と同じ 546ec35 で、差分が空だった。
  PR #467 の head は `claude/todo-157-cube-colour`（2e0cea5、analyzer 0.88.1）。こちらを測った。
- 食い違いは他に無い（実害は未確認の観点を除く）。

## 測り方
- PR 版（8765）と origin/main 版（8766、0.88.0）を並べて起動。tools/live_view.py のブラウザ（CDP 9222）に新しいコンテキスト（390×844、倍率 3）でつなぎ、
  samples の screen-app-grey-shot を盤面まで読み、`BgApp.update` でキューブと対戦を設定。スクリプト: ~/tmp/todo157-check.py
- 状態 4 通り: 中央(64) / 持った(white・4) / ダブルされたところ(white・2・offered) / クロフォード(5 ポイント、white 4 点、中央)

## 1. 色の値（evaluate で読んだ値、4 通りとも同じ）
| 要素 | fill | stroke | stroke-width |
|---|---|---|---|
| 四角（属性） | #f6eedb | #8b1a2b | 2.5 |
| 四角（computed） | rgb(246, 238, 219) | rgb(139, 26, 43) | 2.5px |
| 文字（computed） | rgb(139, 26, 43) = #8b1a2b | none | （stroke が none なので無関係） |

一致。main 版は 四角 #fafafa / #0008 / 1.5、文字 rgb(34, 34, 34) だった。

## 2. 画像（~/tmp/playwright-mcp/todo157-{pr,base}-{centre,held,offered,crawford}.png）
- 4 通りとも、アイボリー地にえんじの縁・文字で出ている。「64」「4」「2」「Craw/ford」が欠けたり縁からはみ出したりしていない（画像で確認）。
- 大きさと位置: 四角と文字の getBBox（x・y・幅・高さ）が、4 通りとも main 版と完全に同じ。

## 実害は未確認だが気づいたこと（判断は管理者）
- クロフォードの文字の右端が縁の内側に近い。四角は x=-42..-2（幅 40）、縁 2.5 の内側は -40.75..-3.25。文字の bbox（1 行目）は -39.59..-3.53 で、
  内側に収まるが右の余白は 0.28 しかない（main 版は縁 1.5 で余裕があった）。画像では接していない。
- 最初の撮影で `.board-wrap` の先頭が写真側（#photo-wrap）だった。盤面側（`:not(#photo-wrap)`）に直して撮り直した。測った値は盤面側のみ。

## 確かめなかったこと
デザインの良し悪し、テスト、他の画面、タップ（依頼どおり）。

## 後始末
サーバーを止め、worktree（todo157-verify・todo157-base）を消した。コードは変えていない。
