# TODO-027 reviewer への依頼

## 目的
ブランチ `claude/todo-027-dark-checkers-impl`（PR #112）の差分 `git diff origin/main...HEAD -- recognizer/board.py` を、
規約と設計に照らしてレビューする。コードは直さない。

## 変更の要旨
- `column_texture`: 列ごと・深さ（駒の個数）ごとに、円の中の |gx|/|gy| の比を、同じ列（上/下）の 12 列の中央値と比べ、
  "shown"（三角形の辺が見える）／"hidden"（隠れている）を返す
- `detect_checkers`: "shown" の位置（`_slot_of` で最も近い位置）の Hough 円を捨てる。ただし同じ列に "shown" でない円が
  2 個以上あり、それと縦に続く（x 0.25 個分以内・y 1.3 個分以内、つながりをたどる）円は捨てない（強い斜めの写真で山の根元を捨てていた）
- `add_hidden_stacks`: 深さ 1 から続けて "hidden" の列（深さ 0 が "shown" でない、円が 1 個以下）に、
  円の出ない駒を足す。`recognize` の中で `count_from_circles` の直前に 1 回だけ呼ぶ
- recognizer 0.11.0（main が 0.10.0 を先に使った）、`recognizer/README.md` の説明、`docs/PI_CHECKS.md` の PI-022

## 見てほしいこと
- 分岐・条件式の意味（深さ 0 の扱い、円が 1 個以下の数え方、`_slot_of` の列の許容 0.3 個分、
  `column_texture` の中央値が NaN になる場合、`add_hidden_stacks` のパッチ切り出しが画像の端ではみ出す可能性）
- `count_from_circles` が足した円（score = CIRCLE_MIN_SCORE）をどう扱うか（LONE_MIN_SCORE、色の 2-means、バー）との整合
- README の説明とコードの食い違い
- CLAUDE.md の「バージョン」「精度の確認」の決まりに沿っているか

## 見なくてよいもの
- しきい値の値そのものの良し悪し（Pi で全サンプルを測って決めた。測り直しは不要）
- 精度の再測定（別の担当がやる）
- `archives/` と TODO.md の書式

## 報告
`archives/agents/TODO-027/reviewer-report.md` に、指摘ごとに「場所・何が問題か・起きる条件」を書く。
問題が無い観点は 1 行でよい。実害を確かめていないものは「実害は未確認」と添える。境界線上の判断は報告だけにする。
返事は「終わったか・報告ファイルのパス・判断が要る点」だけにする。
