# TODO-153 の分担

- main: ユーザーとの対話と判断（保存済みの食い違いの扱い、`CRAWFORD_CUBE` を残すか、読み取りで知らせるか）
- implementer（Opus 5.5 / medium）: `analyzer/static/app.js` の同期の実装、保存済みの食い違いが入る経路の調査、テスト、PR とマージ、決着。分岐の意味を決める実装と、経路の洗い出しが要るので Opus にした → [implementer-report.md](implementer-report.md)
- reviewer（Sonnet 5.5 / high、2 回）: 挙動と分岐が変わる項目なので、確認とは別に入れた → [reviewer-report.md](reviewer-report.md)
- verifier（Sonnet 5.5 / medium）: マージ後のローカルで、live_view のウインドウに `BG_CDP` でつないで 3 つの操作を各 1 回 → [verifier-report.md](verifier-report.md)
