# TODO-073. 同じ写真が 2 組入っているサンプルを整理する

| | main | 担当 |
|---|---|---|
| 見込み | Opus 5.5 / effort medium | main（作業）+ verifier（Haiku 5.5 / medium） |
| 実施 | Opus 5.5 / effort medium | main（作業）+ verifier（Haiku 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | medium | 56 | 10,262 | 63,629 | 1,948,459 | 89% |
| verifier | Haiku 5.5 | medium | 16 | 2,608 | 37,231 | 201,451 | 11% |
| 合計 |  |  | 72 | 12,870 | 100,860 | 2,149,910 | 計 2,263,712 |

- 立ててから着手まで TODO-071 のマージを挟んだので、`--since '2026-10-16 15:41:00'` で集計した

## きっかけ

TODO-071 の測定で、精度の集計（`evaluate.py`・`check_accuracy.py`）が同じ写真を 2 回数えていると分かった。

- `collected-s5dd7x.jpg` と `tv-vegas-open.jpg`: md5 が同じ
- `collected-h8ilqt.jpg` と `commons-tavli-red-diamond.jpg`: 四隅の候補と測った値が全部同じ

## やったこと

- 全サンプルを 32×32 のグレーに縮めて比べ、重複はこの 2 組だけと確かめた（次に近いのは synth-cube-* と元の photo2・photo4 で、わざと作ったもの）
- h8ilqt と tavli は画素まで同じ（違うのはファイルのメタデータだけ）。正解の盤面も同じで、四隅は h8ilqt が外枠、tavli が内側の面
- s5dd7x と tv-vegas-open は正解が違っていた。写真を見ると 6 ポイントに青が 1 個あり、tv-vegas-open（6 ポイント 1・上がり 6）が正しく、
  s5dd7x（6 ポイント 0・上がり 7）はスマホで直したときに見落としていた
- ユーザーの決定（2026-10-16）: 元の tv-vegas-open・commons-tavli-red-diamond を残し、collected-s5dd7x・collected-h8ilqt を消す
  （tv-vegas-open は正解が合っていて、tavli は出典とライセンスが書いてある）
- 2 組の写真と `*.truth.json` を消し、`check_accuracy.py --update`・`trace_cpu.py --update` で `accuracy_baseline.json`・`cpu_reference.json` を書き直した（どちらも削除行だけ）
- `recognizer/README.md` の「精度」の表（Pi に集めた写真 18 枚 → 16 枚、384 ポイント中 339）と CI の基準の経緯、h8ilqt に触れた行を直した。`samples/CREDITS.md` から s5dd7x を外した
- recognizer の版は上げない（読み取りのコードは変えていない）

## 確かめたこと

verifier の報告は `archives/agents/TODO-073/verifier-report.md`。

- `check_accuracy.py` が通る（42 枚で 1008 ポイント中 915）、`trace_cpu.py check` が通る（54 件すべて同じ）
- 基準の 2 ファイルは削除行だけ
- s5dd7x・h8ilqt が残るのは TODO.md と README の「消した」と書いた行だけ
- README の数値が `accuracy_baseline.json` と合う。「54 枚」と書いていたのを verifier が指摘し（54 件には合成画像 12 件を含む）、42 枚に直した
- `uv run pytest analyzer` 84 件が通る（main）

## 分担の振り返り

- verifier: 5 項目を実行して通ることを確かめ、README の「54 枚」と分母 1008 の食い違いを見つけた。main は件数を baseline の項目数から出していて、合成画像を含めていた
- 見込みと同じ編成で、食い違いは無い
- 次に同じ規模（サンプルの削除と基準の書き直し）をやるなら、同じく main + Haiku 5.5 の verifier 1 回でよい。依頼に「README の数値は baseline から出して比べる」と書いたことで食い違いが拾えたので、数値を書き換える項目ではそれを必ず入れる
