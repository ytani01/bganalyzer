# TODO-058 の分担

- main: 実装（`STEP_TITLES`・`index.html` の最初の `h1`・版 0.40.2・PI-041 の期待）
- reviewer（Opus / high）: 画面タイトルの文字列が変わるので、表示の分岐や他の箇所への影響を見る
- verifier（Haiku 5.5 / medium）: Pi のヘッドレスのブラウザで 4 画面のヘッダーを測る。手順が決まっているので Haiku で足りる

reviewer を先、verifier を後に回す。報告は同じフォルダの `reviewer-report.md`、`verifier-report.md`。

途中で範囲が 2 回広がった（手順表示、アプリ名とアイコン）。どちらも表示の文字と CSS だけで分岐は変わらないので reviewer には回さず、同じ verifier に続けて測らせた（verifier-report.md の「追加の確認」「追加の確認（2）」）。

フッターの版を消す変更は表示の動きが変わるので reviewer にも回した（reviewer-report.md の「追加のレビュー」）。
