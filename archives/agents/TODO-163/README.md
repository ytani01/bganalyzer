# TODO-163 の分担

- implementer（Opus 5.5）: 盤面図の座標が多くの所で `COL.w` や余白に依存するので、取りこぼしを避けるため Opus を充てた（[implementer-report.md](implementer-report.md)）
- reviewer（Opus 5.5）: 寸法の依存の取りこぼしと、CSS の負のマージンがほかの画面・並べる形に効かないかを見た（[reviewer-report.md](reviewer-report.md)）
- verifier（Sonnet 5.5）: 幅 390・800・1280・1100px で盤面図の幅・角の丸み・欠けを Playwright で測り、スクリーンショットを撮った（[verifier-report.md](verifier-report.md)、`verify_163.py`、`shots/`）
