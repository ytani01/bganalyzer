# TODO-143 reviewer への依頼

## 目的

ブランチ `claude/recognizer-dark-checkers`（PR #431）の recognizer の変更を、規約と設計に照らしてレビューする。コードは直さない。

## 対象範囲

`git diff main...HEAD -- recognizer/radial.py recognizer/checkers.py recognizer/board.py`

背景は `TODO.md` の TODO-143 と、`recognizer/README.md` の「暗い黒の駒と、駒の色ごとの画像（TODO-143、recognizer 0.28.0）」と「隠れている」の段落。

変更は 3 つ:
1. `detect_checkers(..., checker_lab=)`: 駒の色ごとの「近さ」の画像でも `radial.find` で円を探し、駒の色の円は縁をその画像で測り直す。その画像でだけ見つかった円は、その色（`WEAK_COLOUR` 未満）でなければ捨てる。`board.recognize` が 1 回読んだあとの色で呼ぶ
2. `_weak_checkers`: 枠から 2 pitch より奥で止まる山と枠の間だけ、`WEAK_PEAK_REL` の弱い山から山と同じ色の円を足す
3. `add_hidden_stacks`: 円が 2 個以上の列では、隣り合う円の間が 1.5 pitch を超える所だけ、間隔に合わせて埋める

## 見てほしいこと

- 分岐と条件式の意味が、README と docstring の説明どおりか（特に 1 の `near_only` の作り方と照合、2 の `short` の選び方、3 の範囲の端）
- CPU で結果が変わる計算が入っていないか（`recognizer/radial.py` の docstring と CLAUDE.md の「精度の確認」。float は使ってよいが、使った所は挙げる）
- `side.py` からの `detect_checkers`・`add_hidden_stacks` の呼び出しへの影響
- 規約（`CLAUDE.md` の「バージョン」: recognizer は 0.28.0 に上げてある）

## 見なくてよいもの

- 精度の数字（CI の accuracy と、手元の `--update` で確かめ済み。1366/1560）。全サンプルを流さない
- 採らなかった案の良し悪し

## 報告

`archives/agents/TODO-143/reviewer-report.md` に、指摘ごとに「場所・何が問題か・起きる条件」を書く。問題が無い点は 1 行でまとめる。
境界線上の判断は報告だけにし、原因の切り分けや直し方の決定はしない。実害を確かめていないものは「実害は未確認」と添える。
返事は「終わったか・報告ファイルのパス・判断が要る点」だけにする。
