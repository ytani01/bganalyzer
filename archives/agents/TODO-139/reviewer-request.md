# reviewer への依頼（TODO-139）

**目的:** 盤の端とバーの隣の列で黒の駒を数え落とす件の直し（`git diff main -- recognizer/`）が、意図どおりで副作用が無いかを見る。
**背景:** `archives/agents/TODO-139/README.md` の「切り分けの結果」。

**見るもの**
1. `recognizer/radial.py` の `PEAK_REL` 0.25 → 0.2。ほかの処理（候補の上限 120 個、`detect_checkers` の判定）との関係で、偽の駒が増える経路が無いか
2. `recognizer/checkers.py` の `alike` と、末尾の「確かな駒から枠まで、駒 1 個分の間隔で並ぶ同じ色の円を足す」ループ。
   条件（`ALIKE_SUPPORT`、`ring_same >= 0.6`、横のずれ 0.15 pitch、間隔 0.6〜1.4 pitch、枠から 1.6 pitch 以内、`clear`）の抜けや、
   空いた三角形の付け根を駒と読む経路（TODO-048 の類い）が開いていないか。`shown` の扱いが前の `keep` の規則と食い違っていないか
3. 同じ位置の候補が 3 つの色の面から重複して `alike` に入ることの影響
4. 版（recognizer 0.27.1）とコメントの書き方が周りと揃っているか

**見なくてよいもの:** 精度の数値（CI の accuracy が全サンプルで見る）、四隅の推定、ポイント 1。
**決まり:** コードは直さない。境界線上の判断は報告だけにし、実害を確かめていないものは「実害は未確認」と添える。全サンプルの evaluate / check_accuracy は流さない。
**報告:** `archives/agents/TODO-139/reviewer-report.md` に、指摘ごとに場所・何が問題か・起きる条件。問題が無い点は 1 行。返事は「終わったか・報告のパス・判断が要る点」だけ。
