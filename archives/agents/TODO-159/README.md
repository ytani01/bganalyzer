# TODO-159 の分担

| 担当 | 受け持ち | 報告 |
|------|----------|------|
| implementer（teammate、Sonnet 5.5） | `index.html` の `#sheet-cube`、`cube.js` の `buttons`・`numberPatch`、`app.js`、`style.css`、README、テスト、版 | [implementer-report.md](implementer-report.md) |
| reviewer（Opus 5.5） | 選択から cube の値への写し方、旧 UI の言い方が残っていないか、テストの強さ | [reviewer-report.md](reviewer-report.md) |
| verifier（Sonnet 5.5） | live_view のブラウザで、中央・数・置く・ダブルを選んで盤のキューブと解析の判定が合うかを見る | [verifier-report.md](verifier-report.md) |

**理由:** 選択から cube の値への写し方と分岐が変わるので、reviewer を入れた。見た目と判定の確認は画面を操作する必要があるので、verifier に分けた。
認識は変えないので精度は測らない。
