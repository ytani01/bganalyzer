# TODO-155 implementer 報告

## 変更点
- `analyzer/static/board-view.js`
  - `COL` に `pip: 40` を足し、`ROW`・`rowY` を廃止、`pipY(side)` を追加（奥は `COL.y0` の上、手前は `COL.y1` の下）。`VIEW` は PIP を含む高さに組み直した（-38..478 → -29..469 付近）。列の並びは「PIP・キューブ・トレイ・スコア・中央キューブ・…・キューブ・PIP」。キューブは今までどおり列の端（`COL.y0` / `COL.y1 - cube`）で、PIP はその外側なので重ならない（`COL` の既存の値は変えていない）
  - `drawPips`: 列の幅（`COL.w`）の札に「PIP」と数字の 2 行。盤の上の札はやめた。`tapPart(..., "colour", onPart)` は同じ
  - `drawMatch`: スコアは列の幅いっぱいの角丸なしのグレー（`#c4c4c4`）の長方形に。キューブは変更なし
- `analyzer/static/style.css`: `.pip-n` を 20px、`.pip-l`（「PIP」の小さい字）を追加
- `analyzer/app.py`・`analyzer/static/app.js`: 0.86.0 → 0.87.0
- `TODO.md`: 実装の 3 項目にチェック（`ローカル:` の行は未）

## 確かめたこと
- `uv run pytest analyzer/test_pwa.py -q`: 32 passed
- 作業ツリーの版を port 8011 で起動し、live_view のブラウザ（CDP 9222）に別タブを開いて `BgBoardView.draw` で描いて画像を見た: キューブ中央（マッチ 7、home right）・黒所有（クロフォード、home left）・白所有（アンリミテッド）。スコア・PIP・キューブは重ならない。PIP の札をタップで `onPart("colour")` が呼ばれる
- 8011 のサーバーは止めた。撮った画像はスクラッチパッドにある（リポジトリには入れていない）

## 残る懸念・範囲外
- `analyzer/README.md` の 74・79・90 行目が「盤の上下の行の PIP の札」「白地の正方形のスコア」のままで古くなる（文書は触らない指示なので未更新）
- 結果の画面は同じ `draw` なので同じに出るはずだが、実画面では見ていない
