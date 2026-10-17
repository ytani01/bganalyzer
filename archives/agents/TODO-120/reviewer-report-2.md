# TODO-120 レビュー 2 回目（reviewer、2026-10-17）

対象: brief3.md の直し（implementer-report-3.md）を足した今の差分。コードは直していない。
壊すと落ちるかを試した変更は、そのたびに元へ戻した（md5 で確かめた）。

要修正: 0 件。検討: 3 件（どれも軽い）。好みの範囲: 1 件。

## 前回の指摘

- 1. 集めた写真に side が残らない: 直った。`sample.js` → `/samples`（`samples.py` で値を確かめる）→ `collected.valid` → `evaluate.run`（`check_accuracy.py`・`collected.py`・`tune.py` もここを通る）→ `import_collected.clean` → `check_corners.measure` で、どれも「無いか `right` / `left`」で揃っている。`side: null` はどこでも通さず、`sample.js` は null を入れないので食い違わない
- 2. 左の H の半回転のテスト: 直った。その行を `pass` に替えると `test_reading_from_the_right_and_the_left` が落ちる（実測）
- 3. Claude の四隅: 直った。`renamed(…, null, sideSent())` は、右からなら Claude の TR を TL に、左からなら BL を TL にする（Node のテストの値と、`TURN` からの手計算が一致）。左右が未選択なら並べ替えないので、送る `side`（なし）と合う
- 4. 履歴のモード: 直った。`historyRecord` に残し、`startPhoto` は履歴（629 行）と編集のやり直し（657 行、`historyRecord(state)` を渡す）では写真のもの、新しい写真（617 行、`kept` が null）では端末のものを使う
- 5. 切り替えで手置きの隅を捨てる: 直った（手置きの隅を付け直して `findAgain` で残す）
- 6. 左右を選ばずに読むと普通のモード: 変わらず。前回どおり問いかけが出るので、実害は小さい

## 担当が決めた 4 点

- 0.68.0 より前の履歴は普通のモードで開く: 問題なし。そのころの四隅は普通のモードの順で置いたものなので、横からで開くほうが食い違う
- 隅の付け直しの基準（写真の上の場所はそのまま、名前だけを新しい向きに）: 問題なし。手で置いた隅は、前の向きで自動で見つけた隅を動かしたものか、前の向きの番号の案内（「手前から見て 1. 左上」）で置いたものなので、前の向きの名前が付いている。担当が書いた例外（前の向きと合わない順で置いた場合）は、利用者がその向きで読まないかぎり起きない
- check_corners.py も合わせた: 問題なし。同じ truth を測る道具で、合わせないと横からのサンプルで四隅の誤差が大きく出る
- Claude の四隅を付け直して使う: 問題なし（上の 3）。ただし、プロンプトは「写真の下にいる人から見た」順を求めるので、Claude が写真の位置どおりに名前を付ける前提になる。横からの写真で Claude がそう答えるかは未確認（ブラウザでの確認の範囲）

## 検討

### 1. 文書に「写真ごとにモードを残す」が無い

- 場所: `analyzer/README.md` の PWA の手順（「選んだ位置とチェックは端末に覚え、次の写真もそのまま始める」）、`README.md`（「チェックと左右は端末に覚えておく」）
- 何が起きるか: 履歴から開き直すと端末の既定ではなく写真に残したモードで開く、という今回の挙動が、どの文書にも書かれていない（`rg` で確かめた）。
  0.68.0 より前の写真は普通のモードで開くことも書かれていない

### 2. 切り替えで隅を残す分岐の条件が、テストで守られていない

- 場所: `analyzer/static/app.js` の `cornersAgain`（`state.corners.length === 4 && state.cornersFixed.some(Boolean)`）
- 何が起きるか: `.some(Boolean)` を `.every(Boolean)` に替えても `test_side.py` の PWA のテストは通った（実測）。テストは代入の行の文字列だけを見ていて、どちらの道に入るかの条件は見ていない。
  既存の test_pwa.py と同じ、文字列で確かめるやり方の限界で、ブラウザでの確認（`- [ ] ローカル:`）で補う範囲。実害は未確認

### 3. `tools/check_pi.py --all` は truth の side を送らない

- 場所: `tools/check_pi.py:73-84`（`check_sample`）
- 何が起きるか: 横からのサンプルが `samples/` に入ったあとで `--all` を付けると、Pi にも手元にも `side` 無しで読ませる。Pi と手元の比較（`same as here`）は両方とも普通のモードなので成り立つが、
  「正解と何点合ったか」は低く出る。既定のサンプル（`DEFAULT_SAMPLES`）だけなら関係ない。実害は未確認（いま `samples/` に横からのサンプルは無い）

## 好みの範囲

- `analyzer/static/app.js` の state の初期値で `storedSide()` を 2 回呼ぶ（`sideMode`・`sideFrom`）。`...storedSide()` の 1 回で足りる

## 問題の無かった観点

- 誰でも送れる `/samples` で side の値を確かめているか: `samples.py:59` で `right` / `left` 以外（`null`・リスト・ほかの文字列）を 422 にする。確かめを消すと `test_samples_api_checks_the_side` が落ちる（実測）
- 普通のモードを変えていないか: `evaluate.run` は truth に side が無ければ `side=None` を渡す。`check_corners` は従来の分岐のまま。`valid`・`clean` は足しただけ。PWA は、横からのモードがオフなら `sideSent()` が null で、`renamed(…, null, null)` は並べ替えない
- `test_side.py` は元のまま 15 passed。担当が試した 7 件に加え、H の半回転を消す → 落ちる、`/samples` の確かめを消す → 落ちる、を確かめた

## 作り込みすぎ

作り込みすぎ: なし（`renamed` は Claude の四隅と切り替えの 2 か所で使い、`TURN` の 2 つの値で済んでいる）
