# TODO-173 reviewer の報告

対象: `git diff origin/main...HEAD`（49214f9・18a23d6）。サンプルでの一致は測っていない（verifier の担当）。

## 要修正（1 件）

### recognizer/README.md:105 「箱の和は `cv2.boxFilter`」が `exact.box_sum` に合わない

- 問題: 書き換えで「範囲の引き伸ばしは NumPy の整数、箱の和は `cv2.boxFilter` の float64 で足す整数」とした。
  しかし読み取りの箱の和はもう 1 つあり、`exact.box_sum`（`recognizer/exact.py:296`、`geometry.py:101-102` の
  縁の強さで使う）は今も NumPy の整数の累積和のまま。この行は TODO-046（15b30fb）で書かれ、`exact.py` の関数
  の説明として `box_sum` も含んでいた。今の書き方だと、読み取りの箱の和がすべて `cv2.boxFilter` に替わったと読める。
- 根拠: `rg -n "box_sum\(" recognizer/` → `geometry.py:101`・`:102` から呼ばれ、中身は `np.cumsum`（実際に読んだ）。
- 直し方の例（参考）: 「箱の和は NumPy の整数（`exact.box_sum`）か、`cv2.boxFilter` の float64 で足す整数（`radial.py` のぼかし。…TODO-173）」のように両方を書く。

## 検討（0 件）

なし。

## 好みの範囲（1 件）

- `recognizer/radial.py:73` のコメント「np.partition's answer, faster on these small integers」: 「なぜ」は書けている。
  値の上限（Sobel 3×3 の 16 ビットで勾配の 2 乗は約 208 万まで → `bincount` の配列も 208 万要素）を添えると、
  将来 Sobel の大きさを変えたときに気づける。直さなくてよい。

## 等価性（問題なし）

コードを読んだうえで、旧版の関数を写して新版と手元で比べた（乱数の入力。サンプルは流していない）。

- `radial._box`: 窓の位置は旧版（`h = w // 2`、偶数の w なら i-h..i+h-1）と OpenCV の既定の anchor（ksize/2）で同じ。
  呼ぶ側の `b` は `| 1` で常に奇数。和の上限は 100 × 2 × 1443 × 画素数 ≪ 2^53 で丸めは起きない。
  実測: 6 通り（窓が画像より大きい 40×30 に w=61、1×1、値 1e11 まで、0 が 7 割）で `np.array_equal` かつ int64 → 全一致
- `radial._maps` の閾値: `searchsorted(cumsum(bincount), k, "right")` は「数えて k 個より多くなる最小の値」= `partition(k)[k]`。
  実測 200 通り（長さ 1〜5000、重複多め、k が端も含む）で一致。`mag2` は int64・非負で `bincount` が使える
- `radial._maps` の票: 両側をまとめても整数の数と整数の重みの和で、float64 の和は正確。`orient` の dtype も int64 のまま
- `dice._bodies`: 比べる式・順番（i の昇順）・背景の除外は同じ。int32 と float の比べ方も旧版と同じ（float64）
- `exact.min_area_rect`: `p` は float64 に揃えてから計算するので、旧版の `float()`＋`math.sqrt` と numpy の要素ごとの演算は同じ IEEE の 1 演算。
  長さ 0 の辺の除外、全部 0 のときの戻り値、`argmin` の最初＝旧版の `<` も同じ。重なった点・2 点・3 点の退化した入力でも落ちない（実測）。
  **呼ぶのは `dice.py:54` だけで、`corners.py` からは呼ばれない**（`rg -n min_area_rect recognizer/`）。`exact.py` のほかの関数は変わっていないので、四隅の検出の結果は変わらない
- `geometry.fit_columns`: 足し算の順（`(centre + off) + (arange-2.5)*pw`）、`exact.interp` が多次元でも要素ごと、
  ループの順・`>`・`by_shift`・`v is best` の同一性も保たれている。6 要素の `sum(axis=2)` と 1 次元の `sum()` は
  実測 50×31×97 通りで `repr` まで一致
- `geometry._run_at`: 呼ぶ側の `line` は 2 か所とも bool の配列（比べた結果）なので `tobytes` は 1 要素 1 バイト。
  `k` が `np.int64` でも `bytes.find` に渡せる。実測 2 万通り（他の配列の一部を切り出したものも含む）で旧版と一致。
  戻り値の `lo`・`hi` が Python の int になり中心が `float`（旧版は `np.float64`）だが、値は同じで JSON でも同じ
- 版: `recognizer/board.py` 0.29.1 → 0.29.2（結果が変わらない直しの patch）で CLAUDE.md どおり。`analyzer` は触っていない

## 測る道具（問題なし）

- `record_reading.py`: `pos.to_dict()` と `info` 全体（home・home_guess・bottom_colour・dice・cube・geometry・layout・pitch・
  checker_lab・board_lab・tilt_deg・warnings・side など）を JSON に通して比べる。side の組は truth の `side` を渡すので通る
  （`collected-red-blue-oblique` で `info["side"]` が出ることを確かめた）。2 組で `default=repr` に落ちる値は 1 つも無く、
  numpy の配列が `...` で省かれて比べ漏れることは無い
- 呼び方は evaluate.py と同じ（truth の home、bottom_colour 0）。home・colour の推測（`auto`）は通らないが、どちらも
  `runs`・`bar` だけから決まるので、points・bar が一致すれば同じになる
- `ab_time.py`: 版ごとに別プロセスで `board` の場所を assert で確かめており、取り違えは起きない

## 作り込みすぎ: なし
