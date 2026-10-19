# TODO-143 の分担

- main: 切り分けと実装（写真を見ながら値を測って試す作業で、切り離しにくいため）
- reviewer（Opus 5.5 / high）: 差分のレビュー（分岐と条件式が変わるため）。`reviewer-request.md`・`reviewer-report.md`
- verifier（Haiku 5.5 / medium）: 変更を 1 つずつ外すと読みが変わるか。`verifier-request.md`・`verifier-report.md`。測るスクリプトは `wrong_points.py`

TODO-139 の振り返りに従い、reviewer・verifier は CI の accuracy が通ってから起こした。
