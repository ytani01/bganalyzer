# TODO-143 reviewer の報告

対象: `git diff main...HEAD -- recognizer/radial.py recognizer/checkers.py recognizer/board.py`（ブランチ `claude/recognizer-dark-checkers`）。

実測に使ったスクリプトは scratchpad に置いた（リポジトリには入れていない）。測ったのは collected-galaxy-screen-7、commons-leather-cups、photo-black-blue-oblique（横から。`analyzer/test_side.py` の `raw` と同じ作り方）の 3 組だけ。全サンプルは流していない。

## 要修正

### 1. `recognizer/checkers.py:168-170, 182, 236-238` — 両方の色の画像で見つかった円に、どちらの色の画像かが勝手に 1 つ割り当たる

- **何が問題か:** `near_only` は `((x, y, r), 色の番号)` の set で、`{k: i for k, i in near_only if k not in plain}` で dict にしている。同じ `(x, y, r)` が 2 つの色の画像の両方で見つかると、set を回る順で後に来た方の番号だけが残る。238 行目はその 1 つの色とだけ比べて捨てるので、もう一方の色の円は「その画像で見つかった色をしている」のに捨てられる。コメント（`found in a checker colour's image only: it must have that colour`）と README（「その画像でだけ見つかった円は、実際にその駒の色でなければ捨てる」）の説明と合わない。
- **なぜ起きるか（読んだコード）:** `radial.py` は勾配の向きの両側に票を入れる（明るい円も暗い円も山になる）。だから「白への近さ」の画像にも黒の駒の円が出て、両方の画像に同じ位置・半径の円が出やすい。
- **実測:**
  - collected-galaxy-screen-7: 色の画像の円 30 個と 31 個のうち 12 個が、2 つの画像で `(x, y, r)` まで同じだった
  - commons-leather-cups: 3 個が同じ。そのうち (136, 204) と (134, 279) は、色 1 との差が 4.4 と 9.7（`WEAK_COLOUR` = 12 未満）なのに、色 0 の番号が残ったので、色 0 との差 87.2 と 94.5 で捨てられていた。残りの (136, 127) は色 1 とも 13.8 で、どちらで比べても捨てられる（README が挙げているカップの口の 13.9 はこれと思われる）
  - commons-leather-cups の結果は、「見つかった画像のどれかの色に近ければ残す」に替えても同じ 15 ポイント（読みも同じ）。**ポイントへの実害は未確認**（ほかの組は測っていない）
- どちらの番号が残るかは float のタプルの hash と set の入れ方で決まるので、機械によらず同じになると思われる（未確認）。CPU による違いの心配は無いが、何に比べるかが意図と関係のない順で決まる。

## 検討

### 2. `recognizer/checkers.py:293`（と `board.py:140-150`）— `_weak_checkers` が足す駒が、駒の大きさの測り直しと盤の色の学び直しに入る

- **何が問題か:** `_weak_checkers` は `detect_checkers` の中で毎回動くので、`board.py:140` の結果（駒の大きさの測り直しに使う中央値の半径）と `board.py:143/150` の結果（盤の色を学び直す mask と色）にも、足した駒が入る。
- **根拠:** `board.py:161` のコメント「last, so that the added checkers do not change the measured pitch or the board colours」と、`recognizer/README.md` の「足すのは数える直前の 1 回だけ（足した駒で駒の大きさの測り直しや盤の色の学び直しが変わると、ユーザーの盤の写真が 1 枚 2 ポイント下がった）」が、実測で分かっている罠として残っている。
- **実測:** collected-galaxy-screen-7 では `board.py:140` と `:143` の呼び出しで 2 個、`:150` で 6 個足していた（`checker_lab` 付きの 2 回は 0 個。色の画像で既に見つかるため）。ここで足したのは本物の駒だった。
- 精度の数字にはこの影響が入ったうえで CI が通っているので、**実害は未確認**。README の決まりの例外として扱うのか、決まりに合わせるのかは判断が要る。

### 3. `recognizer/checkers.py:312-315` — `short` のコメントと条件の値が合わない

- **何が問題か:** コメントは「枠から、数え方が補える分より遠くで止まる山」とし、括弧で `count_from_circles` が 2.3 pitch まで補うと書くが、条件は `depth(o[1]) >= 2 * pitch`。深さ 2.0〜2.3 pitch（と `lip`）で止まる山は、数え方が補える範囲なのに対象になる。
- コミット a89a8a2 と README（「山が枠から駒 2 個分より奥で止まるとき（数え方は 2.3 個分までなら枠側の抜けを補う）」）は 2 pitch と書いていて、コードと合っている。食い違っているのはコメントの「by more than the count makes up for」だけ。どちらに揃えるかは判断が要る。
- その範囲で駒を足しても、`count_from_circles` の数（いちばん奥の深さで決まる）は変わらないはずだが、色の 2-means に入る駒は増える。**実害は未確認**。

### 4. `recognizer/checkers.py:314-315` — `short` の元になる円に、1 個だけの円やバーの円も入る

- **何が問題か:** `short` は `out` の円のうち、同じ列でそれより枠側に円が無いものを全部取る。README と docstring は「山」と書くが、コードは 1 個だけの円も、バーの上の円（`in_line` はポイントの列かどうかを見ていない）も対象にする。バーの駒が枠から 2 pitch より奥にあると、バーに沿って同じ色の弱い円を枠まで足す。
- 足すには色（12 未満）・ring（0.6 以上）・縁（0.3 以上）・枠まで 0.5〜1.3 pitch ずつ切れずに続くこと、が全部要るので起きにくい。**実害は未確認**（バーに駒があるサンプルは測っていない）。

### 5. `recognizer/radial.py:113` と `checkers.py:293` — 120 個の上限で、「10% まで」の弱い山が切られる

- **何が問題か:** `_peaks` は強い順に 120 個までしか返さない。`WEAK_PEAK_REL` = 0.1 にすると、山の多い画像では 120 を超え、いちばん弱い山（`_weak_checkers` が拾いたい暗い駒）から切られる。README の「山の 10% までの弱い山を見て」より、実際に見る範囲が狭くなる画像がある。
- **実測:** 10% を超える山の数は、collected-galaxy-screen-7 で 34・36・24〜25（上限の内）、commons-leather-cups の 3 つ目のチャンネル（Lab の b）で 248（上限の 2 倍）。
- **実害は未確認**（leather-cups では `_weak_checkers` の元になる `short` が無く、0 個だった）。

### 6. `recognizer/checkers.py:369-376` と README 194 行目 — 「駒 1 個分より空いていれば」と、実際の値（1.5 pitch）

- **何が問題か:** `int(round((d1 - d0) / pitch)) >= 2` は、中心どうしの間隔が 1.5 pitch 以上（`round(1.5)` は 2）のときに埋める。README は「円と円の間が駒 1 個分より空いていれば」、コードのコメントは「farther apart than one checker」と書いていて、1 pitch を超えれば埋めるとも、縁と縁の間が 1 個分（中心の間隔 2 pitch）とも読める。1.0〜1.5 pitch の間隔は埋めないことを、値で書いたほうが読み違えない。
- 範囲の端（`d1 > pitch * (n + 1)` で外す）は、間に入れる位置がすべて隠れた深さ 1..n（と深さ 0）に収まる条件になっていて、README の「その間だけ」と合う。

### 7. `recognizer/checkers.py:174-177` — `finder="hough"` でも色の画像では `radial.find` を使う

- 比べるための `finder="hough"` で、`checker_lab` があると radial の候補が混ざる（`_weak_checkers` は `finder != "hough"` で止めているが、こちらは止めていない）。docstring は `finder` を「候補の探し方」と書いている。比べるときの数字が radial の分だけ変わる。**実害は未確認**（hough では測っていない）。

### 8. `recognizer/checkers.py:29` — `WEAK_COLOUR` のコメントが使い方の一部しか書いていない

- コメントは「... and colour distance (weighted Lab) to the stack's checker」（`_weak_checkers` の続きとして）だが、`detect_checkers` の 227 行目（色の画像で縁を測り直す円の選び方）と 238 行目（色の画像でだけ見つかった円を捨てる）にも使っている。3 つの使い方が 1 つの値を共有していることが、定数の所から読み取れない。

## 好みの範囲

- `recognizer/checkers.py:30` — `BAR_COLOUR_TOL` の行の空白だけが変わっている（4 → 3 個）。今回の変更と関係が無い。

## 作り込みすぎ

- `recognizer/radial.py:L99-101`: shrink: `rel=None` と `rel = PEAK_REL if rel is None else rel`。`RADIAL_TUNE` の上書きは `def` より前に済むので、`def _peaks(ch, r0, rel=PEAK_REL)` と `def find(channels, r0, rel=PEAK_REL)` で同じ。-1 行。
- `recognizer/checkers.py:L366-371, L383-386`: shrink: `X, Y = ...`・`med = _top_colour(...)`・`out.append(...)` の 3 行が 2 つの分岐に同じ形である。`def add(x, y)` を 1 つ置けば -2 行。
- `recognizer/checkers.py:L308-309`: shrink: 1 か所でしか使わない `colour_gap`。内包表記の中に `np.linalg.norm((np.float32(w[3]) - np.float32(o[3])) * LAB_W)` を書けば -2 行（好みの範囲）。

net: -5 lines possible.

## CPU で結果が変わりうる計算（float を使った所）

CLAUDE.md の「精度の確認」で float は使ってよいので、使った所を挙げるだけにする。

- `checkers.py:173-174`: 色の近さの画像を float32 の `np.linalg.norm`（3 要素の和と sqrt）で作り、`np.uint8(...)` で切り捨てる。+ − × と sqrt だけで、3 要素の和の順が CPU で変わらなければ同じになる。arm64 で同じになるかは未確認。整数の境目のすぐ近くの値だけが 1 違う可能性がある
- `checkers.py:227`: `np.linalg.norm(med - c) < WEAK_COLOUR`（float32）。`edge_support`（float64、cos/sin は丸めてある）は前からある
- `checkers.py:238`、`_weak_checkers` の深さの比べ方と `colour_gap`、`add_hidden_stacks` の `round((d1 - d0) / pitch)` と `int(x + m)`: どれも float の四則演算と切り捨て
- `radial.py:111` の `int(rel * 100)`: 0.1 と 0.25 では 10 と 25（`0.1 * 100` は 10.0 を実測）。整数のまま比べているので CPU によらない

## 問題が無かった点

- `count_from_circles` の 3 つ目の戻り値は `cent = cc / LAB_W`（重みを外した Lab）で、`detect_checkers` が `* LAB_W` して使う向きと合っている。`_weak_checkers` の `med / LAB_W` と `o[3]` も同じ単位で比べている
- `radial._peaks` の cache の key に `rel` が入っている。1 枚の写真で cache は 13 項目になり、`_maps` が消すのは 12 を超えてから新しい画像の map を入れるときなので、同じ写真の中で作り直しは起きない（コードを読んで数えた）
- `_weak_checkers` の `while` は 1 回ごとに 0.5 pitch 以上枠へ近づくので必ず止まる
- `add_hidden_stacks` の円が 1 個以下の列の処理は、前と同じ条件（`sum(...) > 1` と `len(stack) < 2`）
- `side.py` への影響: `detect_checkers` は `checker_lab` 無しで呼ばれ、色の画像は作らない。`_weak_checkers` と `add_hidden_stacks` の変更は横から読む処理にも入る。横から読む photo-black-blue-oblique（`test_side.py` の `raw` と同じ作り方）では `_weak_checkers` が足したのは 0 個で、24 ポイント中 22（`test_side.py` の「22 when measured」と同じ）。`samples/` に横から撮った組（truth に `side`）は無く、CI の accuracy は横から読む処理を見ていない
- バージョン: recognizer だけが変わる機能の変更で、`recognizer/board.py` の `__version__` が 0.27.2 → 0.28.0。analyzer は変わっていないので上げなくてよい
- テスト: recognizer に単体テストは無く、`accuracy_baseline.json` に collected-galaxy-screen-7（24）と良くなった組が入っているので、変更を戻すと CI の accuracy が落ちる
- 文書: README の「集めた写真 37枚」は `samples/collected-*.truth.json` の数（37）と合う。README の「隠れている」の段落と、新しい節の説明はコードの分岐と合っている（上の 3・4・6 の言い方を除く）
- 範囲: 上の空白 1 行のほかに、指示に無い変更は無い
