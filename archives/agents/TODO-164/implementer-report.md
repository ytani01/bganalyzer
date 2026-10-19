# TODO-164 implementer の報告

## 変更
- `analyzer/static/board-view.js:99` 申し出中（`BgCube.offered(scene.cube)`）は `drawWay` を呼ばない。サイコロと同じ条件
- `analyzer/static/board-view.js:304` `drawWay` のコメントに「申し出中は描かない」を追記
- `analyzer/static/board-view.js:294` キューブの地 #1f3f7a、縁 #ffffff
- `analyzer/static/style.css:305-306` `.cube-num` / `.cube-crawford` の fill を #ffffff
- `analyzer/app.py:33`・`analyzer/static/app.js:14` 0.90.0 → 0.90.1
- `TODO.md` TODO-164: 背景に追加の指示、見込みに reviewer、実装の行にチェック、確認とローカルの行に矢印の件

`rg -e f6eedb -e 8b1a2b analyzer/` に出たのはキューブだけ。ほかの色は変えていない。

## 検証
- `uv run pytest analyzer/test_pwa.py -q`: 34 passed（終了コード 0）
- 画面での確認は verifier の担当（未実施）

## 気づいたこと
- `board-view.js:263` の申し出中のキューブの置き場所は矢印との間隔 6 を基準に計算している。矢印が出なくなっても位置は変えていない（「大きさ・位置を保つ」ため）。
