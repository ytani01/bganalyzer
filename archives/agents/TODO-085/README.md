# TODO-085 の分担

- main: 測定・実装（`refine_tips` の `ROW_REACH` の条件を外した）
- reviewer（Opus 5.5 / high）: 条件を外したことで、本当に段の長さが違う写真を崩す恐れが無いかを見る。分岐が変わる項目なので入れた
- verifier（Haiku 5.5 / medium）: photo3〜6 の点数と、条件を戻すと photo6 が落ちることを測る

`probe_tips.py`: `find_tips` を包み、回ごとの段ごとの三角の長さ・付け根と、`lt`・`lb` を出す（photo6 用）。
