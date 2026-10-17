# TODO-104. 斜めの写真で、四隅の推定が盤を外す

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort high | main（測定・実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |
| 実施 | Opus 5.5 / effort high | main（測定・実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | high | 102 | 42,006 | 64,668 | 9,498,846 | 91% |
| reviewer | Opus 5.5 | high | 34 | 4,120 | 73,130 | 783,012 | 8% |
| verifier | Haiku 5.5 | medium | 8 | 3,398 | 33,969 | 78,423 | 1% |
| 合計 |  |  | 144 | 49,524 | 171,767 | 10,360,281 | 計 10,581,716 |

- reviewer と verifier は定義（`~/.claude/agents/`）のモデル・effort のまま（reviewer は opus / high、verifier は haiku / medium）

## きっかけ

ユーザーが、斜めから撮った写真では盤の縁で一部が隠れることを想定して四隅を補正できないかと尋ね、「手前の壁の上端を取る」件として立てた。
着手して傾きの大きい 6 枚（`view_tilt_deg` 42〜61°）を測ると、その外れ方は 1 枚も無かった。photo5・collected-5wxq9t は見つからず、photo6 は右半分だけを囲み、
commons-rollup-oblique・collected-4b88u3 は盤と違う場所を囲んだ。ユーザーと決めて、「斜めの写真で四隅の推定が盤を外す」件に中身を差し替えた。

## やったこと

- 外れる 5 枚で、正解の四角形の点数を測った（`archives/agents/TODO-104/diag104.py`）。5 枚とも、選ばれた四角形より正解の方が点数は高く、候補に入っていないのが原因だった:
  - ① photo5・photo6: 辺の傾きが上限 0.3 を超える（photo5 の奥の辺 0.36、photo6 の左の辺 0.39）
  - ② collected-4b88u3: 盤が写真の中で 35〜55° 回っている。collected-5wxq9t: 盤が写真の幅の 25% で、探す大きさの下限（30%）で落ちる
  - ③ commons-rollup-oblique: 右の辺の傾き 0.98・縦横比 2.32（上限 2.2）
- ユーザーは①と②を直すことにした。②は向き（どちらが手前か）が写真から決まらないので、向きは決め打ちにすることにした
- `recognizer/corners.py` の `SLOPES` を ±60（傾き 0.3）から ±100（0.5）に広げた。横の縁と縦の縁の候補の両方に効く
- ②として写真を 90° 回しても探す処理を入れたが、2 枚とも拾えなかった（4b88u3 は傾きを 1.0 まで広げても 41%、5wxq9t は大きさの下限）。時間が約 2 倍になるので、ユーザーと決めて外した
- `_Upright` の `pad` は傾き 0.3 に合わせた大きさのまま（`ponytail:` のコメントを付けた）。傾きに合わせても 5 枚の結果は変わらず、メモリが 1.5 倍になる
- `analyzer/test_api.py` の `test_corners_are_found_on_samples` に photo6（5% 以内）を足した
- recognizer 0.23.1 → 0.23.2、`recognizer/README.md` の「四隅の推定」の節

## 確かめたこと

- 全 57 枚の `check_corners.py`（`archives/agents/TODO-104/check_corners-0.23.1.txt`・`-0.23.2.txt`）: 良くなったのは photo5（見つからない → 4.7%）、photo6（23.3% → 3.8%）、
  collected-tad9pt（36.7% → 4.5%）、commons-case-midgame（7.7% → 4.2%）、collected-ajxlol（見つからない → 9.1%）。3.6% 以内の枚数は 35 のまま。時間は合計 26.4 → 30.7 秒
- 悪くなった 2 枚はユーザーが受け入れた（`archives/agents/TODO-104/worse104.py`）: collected-bfqwve（4.3% → 5.7%。盤が写真の上端に接していて、どちらの版でも正解より少し内側の四角形を選ぶ）、
  commons-rollup-oblique（28.5% → 見つからない。どちらの版でも当たらない）
- verifier: 5 枚の値、テストが通ること、`SLOPES` を ±60 に戻すと photo6 でテストが落ちること、README の数値（`archives/agents/TODO-104/verifier-report.md`）
- PR #315 の GitHub Actions の `test` と `accuracy` が通った
- ローカル: マージ後の `/version` が recognizer 0.23.2。アプリと同じく縮めた photo5 を `/find-corners` に送ると、四隅が盤を囲んだ（誤差 4.5%。前は見つからない）

## 残ること

- 盤が写真の中で斜めに回っている写真（collected-4b88u3）と、強い斜めで縦横比が大きい写真（commons-rollup-oblique）は外れたまま。どちらもユーザーが四隅を置き直す

## 分担の振り返り

- reviewer は、README の時間の誤り（7% と書いたが 16%）、「外れた 5 枚」が指す写真の取り違え、`pad` が古い傾きのままなこと、変更を守るテストが無いことを見つけた。4 つとも直した。
  悪くなった 2 枚をユーザーが受け入れたかが差分から読めないとも指摘し、それでユーザーに聞いて調べ直した
- verifier は食い違いを見つけなかった。壊すとテストが落ちることを実測で示した
- 見込みの編成とは食い違わなかったが、前提（手前の壁）が測ってすぐ崩れ、中身を差し替えた。項目を立てるときに `check_corners.py` で斜めの数枚を測っておけば、差し替えの往復が要らなかった。
  次に四隅の推定の項目を立てるときは、立てる前に対象の写真で 1 回測る
