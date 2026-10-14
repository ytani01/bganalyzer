# TODO-038 の分担

- main: 実装（作りを途中で 2 回変えたので、試行錯誤が多い）
- reviewer（Opus 5.5 / high）: 挙動が変わり、公開の入口（/samples）から来るデータを自動の処理に渡すので入れた。
  1 回目は cron と claude -p の作り、2 回目はサーバーが起動する作りを見た
- verifier（Sonnet 5.5）: Pi でイメージを作り直し、別のコンテナに /samples で送って起動と nice を実測する。定義の Haiku では難しいので上書きした

報告: [reviewer-report.md](reviewer-report.md)（1 回目）、[reviewer-report-2.md](reviewer-report-2.md)、[verifier-report.md](verifier-report.md)
