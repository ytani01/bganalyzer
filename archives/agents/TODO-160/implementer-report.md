# TODO-160 implementer 報告

## 変更点
- `analyzer/static/board-view.js:260-270`（`drawCube`）: ダブルされたところのキューブの横を `fieldCx(cube.at)`（ダブルされた人）から、`fieldCx(ダブルした人)` に変えた。縦（`cube.at` の側の半分、真ん中から ±75.25）はそのまま。コメントも直した。
  - 手前がダブル（`cube.at = black`）→ 右の場の奥寄り、奥がダブル（`cube.at = white`）→ 左の場の手前寄り。
- `analyzer/README.md:81`: キューブの場所の説明を直した。
- 版: analyzer 0.88.2 → 0.88.3（`analyzer/app.py:33`、`analyzer/static/app.js:14`）。
- `TODO.md`: TODO-160 のチェック 2 つ（位置、版）を入れた。`ローカル:` の行は未チェック。

## 自分で確かめたこと
- `uv run pytest analyzer/test_pwa.py -q`: 32 passed。
- 位置は式だけで、画像では見ていない（確認は verifier）。位置を見るテストは元から無い（ブラウザが要る）。

## 残る懸念
- 画面での重なり（ダイス位置は出ないので問題ないはず、矢印・チェッカー）は未確認。
- 並行の TODO-159（PR #473）が `TODO.md` を変えるなら、先頭の「残っている項目」の行などでぶつかるかもしれない。
