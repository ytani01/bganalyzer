# TODO-083 確認報告（verifier）

対象: `recognizer/geometry.py` の `fit_columns` に足した OUTER_GAP の補正。コードは変更していない（OUTER_GAP は確認のため一時的に 99 にしたが、元の 1.4 に戻した）。

## 1. evaluate（photo3〜photo6）

終了コード 0。

| 画像 | 結果 | 期待 | baseline | 判定 |
|---|---|---|---|---|
| photo3 | 24/24 | 24 | 24 | 一致 |
| photo4 | 23/24 | 23 | 23 | 一致 |
| photo5 | 22/24 | 22 | 22 | 一致 |
| photo6 | 10/24 | 10 | 10 | 一致 |

photo4 の食い違い（参考、baseline と同じ）: `point 22: truth +0 got -2`
photo5 の食い違い（参考、baseline と同じ）: `point 1: truth -2 got +0`, `point 6: truth -2 got +0`
photo6 の食い違い（baseline と同じ 14 点）は出力のとおり。

## 2. 補正が効いているか（BG_DEBUG_COLS=1、photo6）

stderr の `fit_columns` 行（evaluate 出力より）:

```
fit_columns 0.0 2.675
fit_columns 711.40234375 3.098
fit_columns 0.0 3.878
fit_columns 772.94140625 3.619
```

包んだ `board.fit_columns` の 1 回目（reach=1.2、スクリプト `/tmp/claude-649/-home-ytani-work-bganalyzer/3abe6df6-01f4-411e-ba16-52ef60ab5eb3/scratchpad/probe_fit_columns.py`）:

```
[probe] call#1 reach=1.2 a=598.398 bar=113.004
[probe] cols[:6]=[109.7, 204.5, 299.2, 393.9, 488.7, 583.4]
[probe] cols[6:]=[788.7, 881.4, 974.2, 1066.9, 1159.7, 1252.5]
```

- 右の面 cols[6:]: 788.7〜1252.5。訂正後の期待 789〜1252 と一致（直す前の 721〜1160 とは違う）。
- 左の面 cols[:6]: 109.7〜583.4。期待 110〜583 と一致。

スクリプトは `archives/agents/TODO-083/` ではなく scratchpad に置いた（依頼では archives に残すとあったが、置き場所の指定は確認できていない。下の判断が要る点を参照）。

## 3. 補正を外したときの確認（photo6、OUTER_GAP = 99）

```
photo6.truth.json: 8/24 points correct, bar ok, home guess ok (+0.9), ...
```

期待どおり 8/24 に戻った。補正で 2 点増えている。
食い違いは baseline より増えた点が含まれる（point 4, 6, 16, 18, 20, 24 など）。
home guess は +11.3 から +0.9 に変わった（補正の有無で home の値も動く）。実害は未確認。

OUTER_GAP は `1.4` に手で戻した。`git diff main -- recognizer/geometry.py` で `+OUTER_GAP = 1.4` を確認した。git checkout は使っていない。

## 判断が要る点

- 依頼にあった「`archives/agents/TODO-083/` に残す」スクリプトは、今回 scratchpad に置いた。archives に移すか、どちらでよいかの指示が要る。
- 補正を外したときの home guess の変化（+11.3 → +0.9）は、この確認の範囲では原因も実害も判断していない。

追記: 確認に使ったスクリプトは `archives/agents/TODO-083/probe_fit_columns.py` にも置いた（scratchpad と同じ内容）。
