# TODO-031 の分担

- main: 実装（app.py の例外ハンドラー 2 つとテスト 1 つで、小さい）
- reviewer（Opus 5.5）: レスポンスが変わらないか、入力がログに漏れないかを見る。挙動が変わる項目なので入れた
- verifier（Sonnet 5.5）: 壊すとテストが落ちるか、実際のコンテナのログに出るかを実測する。定義の Haiku では実測から逃げるおそれがあるので上書きした

報告: [reviewer-report.md](reviewer-report.md)、[verifier-report.md](verifier-report.md)
