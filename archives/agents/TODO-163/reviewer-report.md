# TODO-163 reviewer の報告

対象: `git diff origin/main...HEAD`（PR #484）。要修正 0・検討 0・好みの範囲 1。

## 要修正

なし。

## 検討

なし。

## 好みの範囲

- `analyzer/static/board-view.js:82` `x0 = home === "right" ? B.x0 - 8 : …` の `8` は、`sideX` と枠の rect に直書きされている枠の張り出し 6 と、トレイの線の外側 2 の和。枠の 6 を変えると 3 か所を揃えることになる。ただし 6 の直書きは前からあり、コメントで 2 の意味は書いてあるので、このままでもよい

## 確かめたこと（問題なし）

- viewBox（座標を計算して確かめた）: home=right は `12 … 683` で右端 695 = 列の右端 693 ＋ トレイの線 2、左端 12 = 枠の左端 14 − 2。home=left は `-39 … 683` で右端 644 = 枠の右端 642 ＋ 2。詰めた範囲（右の 0〜12、左の 644〜660）に描くものは無い（点の番号・駒・当たり判定は x 20〜636、道の矢印は inset 82 の内側）
- `COL.w` を使う所はすべて `COL.w` から計算している: トレイ（幅・当たり判定）、取ったチェッカーの板（`COL.w - 12` = 31、左右 6 ずつ空く）と数（`off-n` 15px、最大 "15"）、ピップ数の板と文字（中央 `COL.w / 2`。20px bold で 3 桁、上限 375）、点数（20px bold の 2 桁で約 23）、キューブ（`(COL.w - 40) / 2` = 1.5 の内側。縁 1.25 を足しても列の中。"Craw"/"ford" 14px と "64" はキューブの大きさが同じなので前と同じ）、矢印の `off` の終点（`sideX` ＋ `COL.w`）。列の中で `56` などの直書きは残っていない（`rg -n "COL\.w|56|724|660" analyzer/static/*.js`）
- マッチの行（`BAR_X` = 328 の中央寄せ、17px bold）: 最長の「25 ポイントマッチ（クロフォード） ▾」でも幅 260 前後で、home=right の左（328 − 12 = 316）、home=left の右（644 − 328 = 316）に収まる（文字幅は見積もり。実測は未確認）
- `drawArrow` の曲がりは盤の縦の中央へ向くので、`off` への矢印が横に viewBox を出ることはない
- CSS: `.board-wrap` は `index.html` の 2 つ（`#photo-wrap` と `#board-pin` の中）だけで、ほかの画面には効かない。結果の画面は `#board-pin` ごと `#outcome-board`（`display: contents`、`.step` に padding なし）へ移るので、そこでも `main` の padding の上に広がるだけ。`main` は `box-sizing: border-box` で max-width 720 なので、`max-width: 720px` の角の丸み 0 は端に付く幅と一致する
- 1000px 以上の並べる形: DOM の順で写真が左・盤面が右なので、内側を戻す `#photo-wrap { margin-right: 0 }` と `.board-pin .board-wrap { margin-left: 0 }` の向きは合っている。どちらも `#board:not([hidden]) .boards.two` に絞られ、詳細度も `.board-wrap` より高い。1241px 以上では外側も `main` の縁までで、角は 8px のまま
- 縦長のスマホの `.board-pin`（sticky）: 盤面が左右に 16px 出るが、出た分は盤面自身の背景で覆われ、ほかの中身は `main` の内側を流れるので横から透けない（コードを読んだだけ。実機は未確認）
- バージョン: `analyzer/app.py` と `app.js` の `APP_VERSION` がともに 0.90.0（マイナーを上げた。見た目の変更なので CLAUDE.md の決まりどおり）。recognizer には触れていない
- 範囲: 指示外の変更なし。`TODO.md` は実装の 3 行のチェックだけで、`- [ ] スマホ:` の行は残っている
- 文書: README・`analyzer/README.md`・`docs/` に `COL.w`・余白の寸法・旧版の記述は無い（`rg`）
- テスト: 見た目だけの変更で、座標の値を固定するテストは無い。足すものは無いと判断（確かめは verifier のスクリーンショット）
- 作り込みすぎ: なし
