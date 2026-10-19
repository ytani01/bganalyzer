# TODO-173 implementer の報告

## 測る道具（このディレクトリ）

- `record_reading.py` — 四隅を `*.truth.json` に固定し、`board.recognize`（evaluate.py と同じ呼び方: truth の home・side、bottom_colour 0）の出力すべて（`pos.to_dict()` と `info` 全体。geometry・dice・cube・layout・pitch・checker_lab など）を JSON で記録し、時間も残す。`--compare A B` で、出力が完全に同じでない組と時間を出す
  - 使い方: `uv run python archives/agents/TODO-173/record_reading.py OUT.json`（引数なしで全サンプル）
- `ab_time.py` — 前後の recognizer を交互に流し、組ごとの最速で比べる。同じ名前のモジュールを 1 プロセスに 2 つ読めないので、版ごとに常駐の worker プロセスを立てる。`same=` は出力全体のハッシュの一致
  - 使い方: `mkdir old && git archive origin/main recognizer | tar -x -C old` のあと `uv run python archives/agents/TODO-173/ab_time.py old/recognizer 3 samples/x.truth.json ...`
  - worker は環境変数 `RECOGNIZER` で recognizer の場所を `record_reading.py` に渡し、読み込んだ `board` の場所を assert で確かめる

## 時間のかかっている所（cProfile、3 組: cork-green-side（side）・blue-red-top・red-blue-oblique、合計 12.8 秒）

| 所 | 割合（累積） | 中身 |
|---|---|---|
| `radial._maps` | 約 38% | うち `_box`（整数の累積和）が 4 割、`np.partition` が 2 割、`np.bincount` 4 回が 2 割 |
| `dice._bodies`（dice と cube から） | 約 15% | 連結成分 7.5 万個を Python で 1 つずつふるい分け、`exact.min_area_rect` の辺ごとのループ |
| `geometry.find_tips` | 約 14% | `_run_at` の Python の while ループ（5.5 万回） |
| `geometry.fit_columns` | 約 9% | 31×97 の格子で `exact.interp` を 7.2 万回 |

## 直した所（アルゴリズムと計算の順序は変えていない）

- `recognizer/radial.py:44-57` `_box`: 整数の累積和を `cv2.boxFilter`（float64、`normalize=False`、`BORDER_CONSTANT`）に。足すのは 2^53 よりずっと小さい整数なので、どの順に足しても同じ値になる（int64 に戻して返し、`// (b*b)` は今までどおり整数で割る）。float のまま 3 回通して `//` する形も試したが、float の `//` が遅く元より遅くなったのでやめた
- `recognizer/radial.py:73-74` `_maps`: k 番目に小さい値を `np.partition` から `np.bincount` → `cumsum` → `searchsorted` に（同じ値。勾配の 2 乗は 0〜約 208 万の整数）
- `recognizer/radial.py:84-96` `_maps`: 両側（sgn ±1）の票を連結して `bincount` を 4 回から 2 回に（整数の数と、整数の重みの和なので同じ値）
- `recognizer/dice.py:39-48` `_bodies`: 大きさと面積のふるい分けを、`connectedComponentsWithStats` の stats 全体に numpy でまとめて行い、通った成分だけをループする（比べる式は同じ。`a < x` で除いていたのを `a >= x` で残す形に）
- `recognizer/exact.py:358-369` `min_area_rect`: 辺ごとの Python のループを、全部の辺を 1 度に numpy で計算する形に（要素ごとの演算は同じ。最小の面積は `np.argmin` で最初のもの＝元の `<` と同じ）。旧版と 3 万個の乱数の点集合で `repr` まで一致を確かめた
- `recognizer/geometry.py:343-364` `fit_columns`: 31×97 の (scale, off) の得点を numpy でまとめて計算し、最良を選ぶ Python のループ（順番・`>` の比べ方・`by_shift`）は残した。3 組の地の画像で reach と a を変えて旧版と 54 通り比べ、`repr` まで一致
- `recognizer/geometry.py:510-515` `_run_at`: 続く True の端を while ループから `bytes.rfind`/`find` に。旧版と乱数 2 万通りで一致
- `recognizer/board.py:78` recognizer の `__version__` を 0.29.1 → 0.29.2

## 一致と時間（5 組、`ab_time.py` で 3 回ずつ交互、組ごとの最速）

```
collected-cork-green-side          4.56s ->   2.93s  same=True   (side)
collected-blue-red-top             4.98s ->   3.43s  same=True
collected-red-blue-oblique         1.57s ->   1.25s  same=True
collected-tan-far                  4.47s ->   3.24s  same=True
commons-case-dice                  4.74s ->   3.52s  same=True
total 20.31s -> 14.37s
```

5 組とも出力全体が一致し、約 29% 速くなった。全サンプルの一致と時間は verifier が測る。

## 検証

- `uv run ruff check` → 成功（終了コード 0）
- `uv run ruff format --check` → 成功（終了コード 0）
- `uv run pytest analyzer/test_exact.py` → 6 passed（終了コード 0）
- `uv run pytest analyzer/test_side.py` → 17 passed、警告 1（既存の StarletteDeprecationWarning。今回の変更とは関係ない）

## 範囲外で気づいたこと・残る懸念

- **`recognizer/README.md` の 105・679・682 行が古くなる。** 「箱の和は NumPy の整数」「強い勾配は順位（`np.partition`）で選ぶ」「整数の累積和で」と書いてある。中身（どの CPU でも同じ値）は変わらないが、やり方の記述は今の実装と合わない。文書なので触っていない
- `_box` が float64 で正確なのは、和が 2^53 を超えないことによる。地図全体の和は「100 × 2 × 1443 × 画素数」以下（地の画像が 1000 万画素でも約 3e12）なので余裕はあるが、画素数の上限に依っている（docstring に書いた）
- `cv2.boxFilter` の float64 の実装が CPU で違っても、足すのが整数で丸めが起きないので値は同じになる見込み。arm64 では確かめていない（CI の accuracy は x86_64）
- まだ残っている重い所: `_maps` の `np.rint`・`bincount`（数値計算そのもの）、`exact.warp`、`connectedComponentsWithStats`。アルゴリズムを変えずに大きく縮める余地は小さいと見て止めた
