# TODO-172 implementer の報告

## 直した所

時間のかかっていた所（cProfile と line_profiler、3 組で測った）: `_structure`（候補ごとの点数づけ。全体の約 40%）、
`_Upright.__init__`（約 15%）、`exact.warp`・`exact.homography`（約 15%）、YOLO・画像の読み込みなど。
前の 2 つを直した。アルゴリズムと出力は変えていない。

- `recognizer/corners.py:187-215` `_Upright.__init__`
  - 傾きごとの `_shift(ys, k)` を、行ごとの表 `_shift(np.arange(h), k)` を引く形にした（掛け算と整数の割り算が画素数から行数に減る）
  - `(ys // STEP) * width + xs + pad` をループの外で 1 回だけ作る
  - 傾きごとの `cumsum`（int64 で作って int32 へ写す）を、最後に `self.cum` 全体へ 1 回だけかける（int32 のまま。値は数え上げなので溢れない）
- `recognizer/corners.py:291-341` `_structure`
  - Lab の値を 2 倍した整数で、チャンネルごとの面（3 × 画素）に並べ直して計算する。平らな色（中央値）は整数か .5 なので、
    2 倍すれば整数になり、距離の 2 乗の 4 倍も整数で正確に出る。`np.sqrt(d4 * 0.25)` は元の `np.sqrt(einsum(d, d))` とビット単位で同じ
    （元も .25 の倍数の和で丸めが起きていなかった）
  - 中央値は `np.median` の代わりに `np.partition` で真ん中の 2 つを取り、`(lo + hi) // 2` で「2 倍の中央値」を出す（偶数個のとき np.median は真ん中 2 つの平均）
  - 「先端の間が平ら」の割合も同じ整数で数える（`< 400` を `< 4 * 400` に）
  - 相関の計算（`v - 平均`、`n`、`c`）は元の式・形・並びのまま（float の足し算の順序を変えないため）
  - 関数の 1 行目より後ろにあって docstring になっていなかった説明文を先頭に移した
- `recognizer/board.py:78` recognizer の版 0.28.0 → 0.28.1
- `TODO.md` の TODO-172 のチェックボックス 4 つを入れた
- 道具（`archives/agents/TODO-172/`）
  - `record_corners.py`: 全サンプルの四隅と時間を JSON に記録する（`check_corners.py` の既定と同じ呼び方。`side` のある組は `side.find_corners_side`）。`--compare A B` で四隅の完全一致と時間を比べる
  - `ab_time.py`: 古い `corners.py` と今のものを 1 つのプロセスで交互に呼び、組ごとの最速の時間を比べる（混んだ機械向け）
  - `corners-before.json` / `corners-after.json`: 書き換えの前と後の記録（87 組）

## 一致の結果

`record_corners.py --compare corners-before.json corners-after.json`: **87 組すべてで四隅が完全に同じ**（`differing corners: 0`）。
試行錯誤の段階では、3 組から集めた 428 個の視点画像で `_structure` の戻り値がすべて同じことも確かめた。
`ab_time.py` の比較でも全組 `same=True`。

## 前後の時間

開発機は、ほかの担当の pytest などで負荷が高く（load average 7〜10）、1 回きりの壁時計の時間は 2 倍ほどぶれる。

全サンプル（record_corners.py、各 1 回）:

| | 前 | 後 |
|---|---|---|
| 合計 | 62.8 s | 60.9 s |
| 組ごとの比（後 / 前）の中央値 | | 0.89 |

遅い組の上位（前の順）:

| 組 | 前 | 後 |
|---|---|---|
| collected-galaxy-screen-1 | 1.73 s | 0.73 s |
| collected-diagram-grey-far | 1.52 s | 0.67 s |
| collected-app-green-shot | 1.42 s | 0.76 s |
| synth-cube-photo-carved-brown-top-8 | 1.11 s | 0.69 s |
| collected-green-black-case-top | 1.07 s | 0.77 s |
| tv-vegas-open | 1.04 s | 0.65 s |
| commons-leather-cups | 1.02 s | 0.81 s |
| collected-xg-shot | 1.01 s | 0.99 s |

合計がほとんど減っていないのは、後の実行で速い組が 2 倍ほど遅く出たため（collected-tan-black-side-2 0.35 → 0.93 s など）。
その組を `ab_time.py`（交互に 5 回、最速）で測り直すと遅くなっていない:

| 組 | 前 | 後 |
|---|---|---|
| collected-tan-black-side-2 | 0.44 s | 0.41 s |
| collected-red-glitter-oblique | 0.60 s | 0.46 s |
| collected-tan-far | 0.78 s | 0.66 s |
| collected-galaxy-screen-1 | 0.91 s | 0.70 s |
| 4 組の合計 | 2.74 s | 2.22 s（−19%） |

ほかの 4 組（galaxy-screen-1・leather-cups・diagram-prime・blue-red-top）でも 4.09 s → 3.52 s（−14%）。
`_structure` だけを 428 個の視点画像で比べると 0.93 s → 0.57 s（−39%）。
**四隅の検出全体で 15〜20% ほど速くなった、というのが確かな言い方。** 静かな機械で測り直せばもっと揃った数字になる。

## 検証

| コマンド | 結果 |
|---|---|
| `uv run python archives/agents/TODO-172/record_corners.py …`（前・後）と `--compare` | 87 組一致 |
| `uv run pytest analyzer/test_side.py -q`（`_Upright` を side.py も使う） | 17 passed、終了コード 0。警告 1 件は starlette の DeprecationWarning（前からある） |
| `uv run ruff check recognizer archives/agents/TODO-172` | All checks passed |
| `uv run ruff format --check` | 整形済み |

## 残る懸念・範囲外で気づいたこと

- 全サンプルは「前」1 回・「後」2 回流した（1 回目の「後」の後に `_structure` の中央値も直したため）。一致の確認は最後の版でのもの
- まだ時間のかかる所: `exact.warp` と `exact.homography`（候補ごとに 1 回ずつ）、`_inner` の中央値、YOLO。`exact.py` は盤面の読み取り（TODO-173）も使うので触っていない
- `_structure` と `_inner` が同じ視点画像を別々に `cvtColor` している（小さいので触っていない）
- 中央値を取る範囲が空になると、元は `np.median` が NaN を返し、今は `np.partition` が例外を出す。今の定数（RW // 2 = 104 でも幅は 38 画素以上）では空にならない
