# TODO-158 implementer 報告

## 変更点
- `analyzer/static/board-view.js:265` `drawCube`: ダブルされたところ（`inField`）の縦を `MID` から、出された側の半分の中ほどへ。`y = MID + (cube.at === "white" ? 1 : -1) * (B.y1 - B.y0) / 4 - size / 2`（手前＝white は下、奥＝black は上。真ん中と端の間の中ほどで、MID から ±98）。横・大きさ・色・タップ（`tapPart`）・列のキューブの `cubeY` は変えていない
- 同ファイルの `drawCube` のコメントに縦の位置を 1 行足した（258 行付近）
- `analyzer/README.md:81` のキューブの説明（盤の中の位置）に「縦はその側の半分の中ほど。手前は下、奥は上」を足した
- analyzer 0.88.1 → 0.88.2（`analyzer/app.py`、`analyzer/static/app.js` の `APP_VERSION`）
- `TODO.md` の TODO-158 の実装 2 項目にチェック

## 自分で確かめたこと
- `uv run pytest analyzer/test_pwa.py`: 32 passed
- `node` で `board-view.js` の構文を読み込み、通った
- 画面は見ていない（verifier の担当。チェッカー・矢印との重なりは未確認）

## 残る懸念
- 中ほど（MID ± 98）は、ポイントの駒の段（5 段目以降）や「次に振る人」の矢印の線と重なる可能性がある。実際の重なりは verifier が画像で見る
- 盤の画面と結果の画面は同じ `drawCube` を通るので、別の対応はしていない（結果の画面で見ていない）
- worktree では `analyzer/test_api.py::test_version_reports_both_parts_and_commit` が `.git` がファイルのため落ちる（TODO-157 と同じ。範囲外、直していない）
