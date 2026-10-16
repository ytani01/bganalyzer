# TODO-084 の分担

- main: 実装（recognizer・API・PWA・文書）と、photo6 など 4 枚の測定（`measure_keep.py`）
- reviewer（Opus 5.5 / high）: 読み取りの分岐とチェックの状態遷移が変わる項目なので入れた。既定の読みが変わらないか、状態の漏れ、文書との食い違いを見る
- verifier（Haiku 5.5 / medium）: テストのファイル 1 本、README の photo6 の行の再現、PWA を Playwright で操作してチェックの入り外れと四隅が動かないことを測る（`check_ui.py`）

`measure_keep.py`: サンプルごとに、四隅を合わせ直す（既定）と固定するの 24 ポイント中の一致数を出す（アプリと同じく縮める）。
