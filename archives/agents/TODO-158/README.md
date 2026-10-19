# TODO-158 の分担

| 担当 | 受け持ち | 報告 |
|------|----------|------|
| implementer（teammate、Sonnet 5.5） | `board-view.js` の `drawCube` の縦の位置、`WAY` の定数、README、版 | [implementer-report.md](implementer-report.md) |
| verifier（Sonnet 5.5） | live_view のブラウザで、2 サンプル（疎・密）× ダブルされた人が手前・奥の 4 通りの位置と、チェッカー・矢印・ポイントの数字とのすきまを測り、画像で見る。直すたびに測り直した（3 回） | [verifier-report.md](verifier-report.md) |

**理由:** 位置の式だけで分岐は変わらないので、reviewer は入れなかった。見た目の確認は画面を操作して測る必要があるので、verifier に分けた。
認識は変えないので精度は測らない。
