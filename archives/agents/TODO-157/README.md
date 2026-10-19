# TODO-157 の分担

| 担当 | 受け持ち | 報告 |
|------|----------|------|
| implementer（teammate、Sonnet 5.5） | `board-view.js` の `drawCube`、`style.css`、版 | [implementer-report.md](implementer-report.md) |
| verifier（Sonnet 5.5） | live_view のブラウザで、キューブ 4 通り（中央・持った・ダブルされたところ・クロフォード）の色の値と大きさ・位置を読み出し、画像で見る | [verifier-report.md](verifier-report.md) |

**理由:** 色を変えるだけで分岐は変わらないので、reviewer は入れなかった。見た目の確認は画面を操作して画像で見る必要があるので、verifier に分けた。
認識は変えないので精度は測らない。
