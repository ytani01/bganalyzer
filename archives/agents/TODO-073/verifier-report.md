# TODO-073 確認報告（verifier）

作業ツリー（ブランチ claude/todo-073-duplicate-samples、未コミット）を確認した。コードは変更していない。

## 1. `uv run python recognizer/check_accuracy.py`: 合格（終了コード 0）

```
points: 915/1008 (baseline 915)
EXIT=0
```

## 2. `uv run python recognizer/trace_cpu.py check`: 合格（終了コード 0）

```
A: {'machine': 'x86_64', 'recognizer': '0.22.0', 'opencv': '5.0.0', 'numpy': '2.5.4', 'cpu': 'SSE SSE2 SSE3 *SSE4.1 *SSE4.2 *AVX *FP16 *AVX2 *AVX512-SKX?'}
B: {'machine': 'x86_64', 'recognizer': '0.22.0', 'opencv': '5.0.0', 'numpy': '2.5.4', 'cpu': 'SSE SSE2 SSE3 *SSE4.1 *SSE4.2 *AVX *FP16 *AVX2 *AVX512-SKX?'}
first different steps: {}
0 of 54 samples read differently
same as the reference: every step of every sample
EXIT=0
```

## 3. `git diff --stat HEAD`: 合った

```
 TODO.md                             |  10 +-
 recognizer/README.md                |   5 +-
 recognizer/accuracy_baseline.json   |   2 -
 recognizer/cpu_reference.json       | 307 ------------------------------------
 samples/CREDITS.md                  |   2 +-
 samples/collected-h8ilqt.jpg        | Bin 883854 -> 0 bytes
 samples/collected-h8ilqt.truth.json |   1 -
 samples/collected-s5dd7x.jpg        | Bin 613996 -> 0 bytes
 samples/collected-s5dd7x.truth.json |   1 -
 9 files changed, 9 insertions(+), 319 deletions(-)
```

- `accuracy_baseline.json`: 削除 2 行のみ（`collected-h8ilqt` と `collected-s5dd7x` の行）。追加行 0。
- `cpu_reference.json`: 削除 307 行のみ。追加行 0。
- 9 ファイルのうち、`TODO.md`・`recognizer/README.md`・`samples/CREDITS.md` 以外は指示どおりの 4 ファイル（サンプル 2 組）と基準 2 つ。範囲は合っている。
- 挿入 9 行は TODO.md 10 行、README 5 行、CREDITS 2 行の差分の合計として出ている。`samples/CREDITS.md` は、Las Vegas の配信の画面の一覧から `collected-s5dd7x` を外しただけ（文面は確認していない）。
- 指示にない変更は見つからなかった。

## 4. `rg -n -e s5dd7x -e h8ilqt --glob '!archives/**'`: 残ってよいものだけ（合った）

```
TODO.md:132:- `collected-s5dd7x.jpg` と `tv-vegas-open.jpg`: md5 が同じ
TODO.md:133:- `collected-h8ilqt.jpg` と `commons-tavli-red-diamond.jpg`: ファイルは違うが、四隅の候補と測った値が全部同じ。同じ写真の大きさ違いらしい
TODO.md:135:- [x] h8ilqt と tavli-red-diamond が同じ写真かを確かめる（写真を並べた画像と、`*.truth.json` の盤面の比較）
TODO.md:139:決めたこと（2026-10-16 ユーザー）: 元の tv-vegas-open・commons-tavli-red-diamond を残し、collected-s5dd7x・collected-h8ilqt を消す。
TODO.md:140:h8ilqt と tavli は画素まで同じ。s5dd7x の正解は 6 ポイントの青 1 個を見落としていて、tv-vegas-open の方が合っていた。
recognizer/README.md:83:  TODO-073 で、ほかのサンプルと同じ写真だった collected-s5dd7x・collected-h8ilqt を消した（54 枚で 1008 ポイント中 915。ほかは変わらない）
recognizer/README.md:479:試して採らなかったもの: 列ごとに「真ん中が面の色でない」だけ点数を引く（中央に模様のある盤 collected-h8ilqt（TODO-073 で消した。commons-tavli-red-diamond と同じ写真）などで 889 → 874）。
RG_EXIT=0
```

- TODO.md の行は項目の経緯。README の 83 行は「消した」と書いた行。479 行は「試して採らなかった」節の中で「TODO-073 で消した」と書いた行で、どちらも指示の範囲内。
- 残りは `archives/` だけで、指示どおり除外。

## 5. README の数値と基準の数値: 合った

`recognizer/check_accuracy.py` の `total()` は、`"synthetic": true` の truth を除いた実サンプルだけを数える（分母は 24 × 実サンプル数）。その定義どおりに数えた。

```
synthetic (除外 12 件): synth-cube-photo2-{2,4,8,16,32,64}, synth-cube-photo4-{2,4,8,16,32,64}
real entries 42   denom 24*42 = 1008   sum points 915
collected real entries 16   denom 24*16 = 384   sum points 339
```

- README の「54 枚で 1008 ポイント中 915」: 実サンプル 42 枚（synthetic 12 件を含めると 54）、1008 は 42 × 24。合っている。
- README の「16 枚・384 ポイント中 339」: collected-* 16 枚 × 24 = 384、points の合計 339。合っている。
- 注意: 「54 枚」は synthetic を含む truth ファイルの総数。`accuracy_baseline.json` の件数も 54 だが、判定の枚数は 42。README の「54 枚で 1008」は、数えた枚数と分母が食い違う書き方になっている。数値自体は一致するので、判断は管理者に任せる（直すなら「42 枚」と書く形）。
- 参考: 全 54 件の `points` 合計は 1180。synthetic 12 件を含むので、README の数値とは別物。

## 確かめられなかったこと・判断が要ること

- 特になし。写真の中身と文章の良し悪しは見ていない（依頼どおり）。
- 判断が要る点: README 83 行の「54 枚で 1008」は、枚数 54 が synthetic を含むため、分母 1008 と枚数が合わない。数値は正しい。
