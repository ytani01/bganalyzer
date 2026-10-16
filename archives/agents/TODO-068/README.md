# TODO-068 の測定（駒を物差しにする前提）

- `measure_scale.py ideal`: 正解の四隅から読み取り、遊戯面の横幅 ÷ 駒の直径（canonical の `(2a + bar) / pitch`）を出す。
  44 枚で 12.47〜14.87、40 枚が 13.0〜14.0（外れはバーの広い盤: diagram-holding 14.87、leather-cups 14.74、4b88u3 14.50 と photo3 12.47）
- `measure_scale.py raw`: 写し直す前の写真（800 px）で、半径ごとに放射対称の山（radial.py と同じ計算）と縁の強さ（`checkers.edge_support`）で円を探す。
  縁のはっきりした円の数で半径を選ぶと、ほとんどのサンプルで小さい半径（駒の内側の輪、目、木目）が勝つ
- `corners-trial.diff`: corners.py の `_structure`（三角形）を、駒の大きさの点数に替えた試作。`check_corners.py --app` で
  - 円の数×半径の合い方: ずれ 3.6% 以内 16 枚（MOVE_IN なしは 12 枚）。今の方法は 28 枚（synth-cube を除く 44 枚）
  - 場所ごとに一番外の円を駒とする: 一部のサンプルは直るが、立体の駒（bfqwve）では外の縁を取れない
  - 中心が 12 列に並ぶことも足す: 9 枚
  - 時間は手元で 0.45 秒前後と、今（0.44 秒。うち 6 割が `_structure`）と変わらない
- 結論: ユーザーが、四隅の点数は今のままにして繰り返し（動かした隅・トリミング）を先に作ると決めた（2026-10-16）。
  駒の物差しは TODO-067 で、半径の取り方から考え直す
- ユーザーに選択肢を出したときは「今の方法は 37 枚」と書いたが、synth-cube の 12 枚を含めた 56 枚での値だった。同じ 44 枚では 28 枚（試作の 16 枚より多いことは変わらない）

# 動かした隅とトリミング（corners.py の `fixed`・`crop`）

`check_corners.py --app` の 44 枚（synth-cube を除く）で、ずれ 3.6% 以内 / それより外れ / 見つからない:

| 条件 | 以内 | 外れ | 見つからない |
|---|---|---|---|
| 今まで（何も渡さない。結果は前と同じで、`trace_cpu.py check` も一致） | 28 | 14 | 2 |
| `--fix 1`（左上を正解に置く） | 27 | 12 | 5 |
| `--fix 2`（左上・右上） | 30 | 9 | 5 |
| `--fix 3` | 32 | 7 | 5 |
| `--crop`（正解の外接矩形 + 15%） | 26 | 15 | 3 |
| `--crop --fix 1`（`TRIMMED` を入れる前） | 28 | 11 | 5 |

- 固定した隅から 5%（`NEAR`）より離れた候補は使わない。使うと、固定した隅に合わせて歪んだ四角形が三角形の点数で勝ち、25〜67% 外れた（photo4・screen1・rollup-oblique）。
  合う候補が無ければ「見つからない」を返し、アプリは今の四隅のままにする
- トリミングした写真では、遊戯面の幅 5 割・高さ 4 割より小さい候補を使わない（`TRIMMED`）。screen2 が 22.8% → 1.6%。
  代わりに 41% 外れていた 3 枚（4b88u3・tad9pt・rollup-oblique）が「見つからない」になる。盤が小さい 2 枚（5wxq9t・sj1vrx）はトリミングで見つかる（21.7%・1.1%）

# 分担

- main: 測定（`measure_scale.py`、`check_corners.py`）と corners.py。前提の測定と corners.py の判断が続くので main が持った
- implementer（Opus 5.5）: `/find-corners` と PWA（`implementer-request.md` → `implementer-report.md`。確認に `check_pwa.py`）
- reviewer（Opus 5.5）→ verifier（Sonnet 5.5）の順（`reviewer-*.md`・`verifier-*.md`）
