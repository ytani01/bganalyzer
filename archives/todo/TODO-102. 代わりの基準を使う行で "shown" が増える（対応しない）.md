# TODO-102. 代わりの基準を使う行で "shown" が増える（対応しない）

| | main | 担当 |
|---|---|---|
| 見込み | Opus 5.5 / effort high | main（調査）+ reviewer（Opus 5.5 / high） |
| 実施 | Opus 5.5 / effort 不明 | main のみ |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | 不明 | 30 | 4,929 | 23,315 | 969,042 | 100% |
| 合計 |  |  | 30 | 4,929 | 23,315 | 969,042 | 計 997,316 |

- コードを変えなかったので reviewer は立てなかった（決めるだけの項目になった）
- main の effort はセッションの設定で、記録に残っていない
- 立てたコミットが見つからなかったので、着手した 2026-10-17 15:20 から `--since` で数えた

## きっかけ

TODO-077 で、`recognizer/checkers.py` の `column_texture` は、行の中央値が `TEX_MIN`（3.0）に届かないとき、
上位 25% の値を基準にするようにした（`TEX_MIN_COVERED` 4.0 以上のときだけ）。
`TEX_SHOWN` は 0.84 なので、その行では上の 3 列前後に必ず "shown" が付く。
斜めの写真で山の側面が上位に入ると、その山の円が `detect_checkers` で候補から落ちうる、と TODO-077 の reviewer が指摘した。

## やらないと決めた理由

`archives/agents/TODO-102/tex_fallback.py`（TODO-077 の `tex.py` を元にした）で、全 65 サンプルについて
代わりの基準を使う行を出し、その行の "shown" を消して（"hidden" だけ残して）読み直した。結果は `tex_fallback.out`。

- 代わりの基準を使う行があったのは 15 枚（collected 6 枚、commons 5 枚、photo5、screen1、synth-cube 2 枚）。
  上位 25% の値は 4.03〜7.79
- 15 枚とも、"shown" を消して読んでも結果は今と同じだった

今のサンプルでは実害が無く、直しても読みが変わらないので、2026-10-17 にユーザーが「対応しない」と決めた。

## 確かめたこと

- 読み直しの比較は `board.recognize` の返す盤面の一致で見た（`alt_same=True`）
- `add_hidden_stacks` が深さ 0 の "shown" を見る分も、同じ差し替えで一緒に比べている
