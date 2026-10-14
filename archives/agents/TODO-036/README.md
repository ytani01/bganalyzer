# TODO-036 の分担

- main: 実装（app.js の分岐 1 か所と、pi_ui_check.py の確認の追加で小さい）
- reviewer（Opus 5.5 / high）: 分岐の意味が変わるので入れた。共有の成功・`AbortError`・その他のエラーの扱いと、user activation の切れを見る
- verifier（Sonnet 5.5）: Pi で `pi_ui_check.py` を流し、直す前に戻すと落ちるかを実測する。定義の Haiku では、ビルドし直す実測から逃げるおそれがあるので上書きした

報告: [reviewer-report.md](reviewer-report.md)、[verifier-report.md](verifier-report.md)
