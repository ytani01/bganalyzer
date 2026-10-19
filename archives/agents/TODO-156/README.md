# TODO-156 の分担

| 担当 | 受け持ち | 報告 |
|------|----------|------|
| implementer（teammate、Sonnet 5.5） | `board-view.js` の `drawCube` と `draw`、README、版 | [implementer-report.md](implementer-report.md) |
| reviewer（Opus 5.5） | 配置の分岐と、古くなる記述の洗い出し | [reviewer-report.md](reviewer-report.md) |
| verifier（Sonnet 5.5） | live_view のブラウザで、ダブルされた人が奥・手前の 2 通りと、ダブルしていない 1 通りを画像で確認 | [verifier-report.md](verifier-report.md) |

**理由:** 描く場所の分岐が変わるので、reviewer を入れた。見た目の確認は画面を操作して画像で見る必要があるので、verifier に分けた。
認識は変えないので精度は測らない。
