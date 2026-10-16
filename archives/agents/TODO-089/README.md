# TODO-089 の分担

- main: 実装（`board.js` の `number` と 2 か所の呼び出し、版、README）
- reviewer（Opus 5.5 / high）: 分岐（手番による番号の向き）が変わるので、`state.onRoll` を使ってよいかを見る。報告は [reviewer-report.md](reviewer-report.md)
- verifier（Haiku 5.5 / medium）: 画面の番号・パレット・最善手の棋譜を Playwright で読み出す。報告は [verifier-report.md](verifier-report.md)、スクリプトは [check_numbers.py](check_numbers.py)（`BG_URL` で接続先を替えられる。マージ後のローカルの確認にも使った）

reviewer を先、verifier を後に回した。
