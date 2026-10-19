# TODO-152 reviewer report

範囲: `git diff origin/main...origin/claude/score-cube-swap-impl`（b93b7b1）。実測・テストはしていない（verifier の分）。

## 要修正

- `analyzer/README.md:81` / 古い記述が残っている / キューブは「持っている人のトレイのすぐ内側に出る」とあるが、
  差分の `cubeY`（`board-view.js:39`）では持ち主のいるキューブは列の上下の端（トレイの外側）に置く。
  クロフォードのときキューブに「Crawford」と出ることも書かれていない。参照も TODO-151 のまま。
- `analyzer/README.md:90` / 古い記述が残っている / スコアは「その人の端（奥は上端、手前は下端）に「3 点」のように出る」とあるが、
  差分の `drawMatch`（`board-view.js:226-231`）では列の真ん中寄り（トレイと中央のキューブの間）に、白地の正方形の札に数字だけで出る。

## 検討

- `analyzer/static/sw.js:2` / CACHE を v59 → v60 に上げているが、要らない変更に見える /
  CLAUDE.md の「バージョン」は sw.js に触れていない。`sw.js` の fetch はネットワーク優先（`fetch(..., { cache: "no-cache" })`、
  キャッシュはオフラインのときだけ）なので、上げなくても新しい board-view.js と style.css が揃って届く。
  直前の見た目の変更の TODO-151 も上げていない。害は無いので、残すか戻すかは管理者の判断。
- `analyzer/static/board-view.js:263-266` / クロフォードのゲームでキューブが片側にある（「解析する」が押せない、誤った）状態でも、
  キューブはその側の端に「Crawford」とだけ出て数が見えなくなる / 要件は「クロフォードのときは数字の代わりに Crawford」で、
  この場合を分けるかは書かれていない。境界線上なので報告だけ（実害は未確認）。

## 確かめて問題なかったこと（1 行ずつ）

- 並び: `cubeY`/`trayY`/`scoreY` から 奥のキューブ・奥のトレイ・奥のスコア・中央のキューブ・手前のスコア・手前のトレイ・手前のキューブ の順、間は `COL.pad`。中央のキューブの中心は列の中心（220）に来る（コードから計算）。
- 札: `rect` は `COL.score` の正方形、`fill="#fafafa"`、`.score-n` は `fill: #222`。中身は数字だけ。
- Crawford の条件: `match && match.length > 0 && match.crawford`。`drawCube` には絞り込み前の `scene.match` を渡しており、アンリミテッドでは `length` が 0 なので出ない。
- アンリミテッド: `drawMatch` の `if (!m.length) return;` が札より前にあり、札は出ない。
- タップの種類: 札は `"match"`、キューブは `"cube"`、トレイは `"home"` のまま。
- コメント: `COL` の上（22-23 行）、`drawMatch`、`drawCube` のコメントは新しい並びと合っている。
- 版: analyzer の機能の変更で 0.84.0 → 0.85.0、`APP_VERSION` も 0.85.0。recognizer は触っていない。
- 範囲: 指示に無い変更は sw.js の CACHE のほか無し。TODO.md は 1 つ目のチェックだけ。

## 作り込みすぎ

- `board-view.js:265`: shrink: `setAttribute` 2 回を、`el("text", {...})` の属性に `...(crawford ? { textLength: size - 4, lengthAdjust: "spacingAndGlyphs" } : {})` で入れれば 1 行減る（好みの範囲）。

net: -1 lines possible.
