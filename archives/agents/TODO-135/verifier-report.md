# TODO-135 verifier 報告

1. 再現: 一致。README の 2 行を外した 3 枚で実行（出力は scratchpad の pred-verify.json）。ずれ・読めた数が表と全 12 値一致。

```
sample               truth | corners.py read   sec |   YOLO read   sec conf | YOLO+crop read
photo4                  23 |       4.5%   15  1.19 |   5.4%   14  0.04 0.88 |      4.9%   23
photo6                  18 |       3.8%   16  0.70 |  10.8%    8  0.04 0.86 |      6.4%   18
collected-er0y2w        20 |       0.0%   19  0.70 |   5.3%   19  0.04 0.89 |      1.2%   21
```
   計（読めた数）: 61 / 50 / 41 / 62 も表と一致。
2. 漏れ点検: 一致。`ds/images` と `ds/labels`（ファイル 502 件）に photo4・photo6・er0y2w・synth-cube を含む名前は 0 件（rg 終了コード 1）。
3. prep.py: 一致。`HELD_OUT` の 3 枚は `real` から除かれ、train にも val にも入らない。`synth-cube*` は `files` の段階で除外。val は `real` からだけ選ぶ。`synth-NNN`（synth.py の合成）は名前が別物。

## 確かめていない / 報告だけ（実害は未確認）
- ファイル名での点検のみ。内容が同じ写真の別名コピー（photo4 由来の別サンプル等）が `samples/` に無いかは見ていない。
- synth.py の合成 60 枚が photo2/photo4 の画像を素材にしていないかは synth.py を読んでいない（prep.py の docstring は synth-cube-* だけがそれ由来と書く）。
- git status: 変更は `archives/agents/TODO-135/`（未追跡。このレポートと既存の `__pycache__` を含む）のみ。コードは直していない。
