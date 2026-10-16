# TODO-094 確認報告

実行: `uv run -q --no-project --with playwright python archives/agents/TODO-094/verify_todo094.py`（終了コード 0）
対象: http://127.0.0.1:8094/ 、chromium `/usr/bin/chromium`、viewport 412x915、写真 samples/screen1.png（home left、bottom_colour 1）。
版: ヘッダーに `a0.58.0 · r0.23.0`。

## 1. 初期状態（盤面の画面）
- `#photo-tools`: 表示（hidden=false、実寸あり）
- `#photo-side`: type=checkbox、checked=true、表示あり
- 文言: 「元の写真を並べる」
- `#photo-wrap`: 表示、実寸 380x299
- `BgApp.state.photoView`: "side"
- `.seg[data-name="photoView"]` の数: 0、`#photo-tools` 内の button: 0

判定: 一致。

## 2. クリックによる切り替え
- 1 回目クリック後: checked=false、`#photo-wrap` hidden=true（実寸 0x0）、photoView="off"。一致。
- 2 回目クリック後: checked=true、`#photo-wrap` hidden=false（実寸 380x299）、photoView="side"。一致。

alerts: なし。

## 3. 画像
- 保存先: /home/ytani/tmp/playwright-mcp/todo094-photo-tools.png（`#photo-tools` の要素撮影。2 回切り替え後、チェックありの状態）
- Read で確認: チェックボックスにチェックが入って表示され、横に「元の写真を並べる」の文言が全部見えている。欠け・重なりは見当たらない。
- 注意: 画像は約 380 px 幅で小さい。細部の判定は粗い（デザインの良し悪しは評価していない）。

## 判断が要る点
- 無し。
- 確かめていないこと: tools/ui_snapshot.py（指示により流していない）、テスト全体、精度、他のボタン・画面。
