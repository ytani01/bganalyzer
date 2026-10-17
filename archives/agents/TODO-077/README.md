# TODO-077 の分担

- main: 測定と実装（写真を見ながら試す作業で、切り離しにくい。TODO-076 と同じ）
- reviewer（Opus 5.5 / high）: `column_texture` の基準の変更が "shown" による候補の除外に与える影響、閾値の置き方、版と README（`reviewer-report.md`）
- verifier（Haiku 5.5 / medium）: 5 枚の読みと、分岐を外したとき・閾値を下げたときに読みが崩れるか（`verifier-report.md`）

`tex.py` は、行（段・深さ）ごとの横 / 縦のエッジの比を出す測定用のスクリプト（`uv run python archives/agents/TODO-077/tex.py samples/<名前>.truth.json`）。
