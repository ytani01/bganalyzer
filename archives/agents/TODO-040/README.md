# TODO-040 の分担

- **main（Opus 5.5）:** 実装。`index.html` と `style.css` の数行で、ファイルをまたぐ込み入った変更ではないので implementer は立てなかった
- **verifier（Sonnet 5.5、定義は haiku を上書き）:** Playwright で 2 つの幅を実測し、スクリーンショットで欠けや重なりを見る。画像を見る判断が要るので Sonnet にした。
  分岐を変えない見た目だけの変更なので reviewer は付けなかった

報告: [verifier-report.md](verifier-report.md)（1〜3 回目）。計測は [check_layout.py](check_layout.py)。
