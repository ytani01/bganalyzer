# TODO-120 直しの報告（implementer、3 回目、2026-10-17）

brief3.md の 5 点を、2 回目の差分（コミット前）に足した。版は 2 回目のまま（recognizer 0.24.0、analyzer 0.68.0）。手法は変えていない。

## 1. 集めた写真に横からのモードを残す

- `analyzer/static/sample.js`: `truth()` が `s.side` を受け取り、あるときだけ `side` を入れる（普通のモードでは入れない）
- `analyzer/static/app.js` の `sampleOf`: `side: sideSent()` を渡す（書き出し・`POST /samples` のどちらも）
- `analyzer/samples.py`: 受け取った truth の `side` は、無いか `right` / `left` だけを認める（ほかは 422）
- `recognizer/collected.py` の `valid`: 同じ確かめを足した。測り直しは `evaluate.run` を通るので、`side` 付きの組はそのモードで読む
- `recognizer/evaluate.py` の `run`: `board.recognize(..., side=t.get("side"))`。`check_accuracy.py` は `evaluate.run` で測るので、横からのサンプルが入ればそのモードで測られ、そのまま基準になる
- `recognizer/import_collected.py` の `clean`: `side` が `right` / `left` のときだけ残す
- `recognizer/check_corners.py`: truth に `side` があれば `side.find_corners_side` で探す（依頼に名前は無いが、同じ truth を測る道具なので合わせた）
- 文書: `analyzer/README.md`（書き出す JSON の説明）、`docs/raspi.md`（`collected/` の中身）、`recognizer/README.md`（横からの節に「サンプル」）

## 2. 左から撮った写真の H の半回転をテストで守る

`test_reading_from_the_right_and_the_left` に 2 つ足した。左から読んだ `geometry["corners"]` が、渡した四隅に重なること。
左から読んだ駒の円（写真の画素）が、右から読んだものと同じ位置になること。
`side.py` の半回転の行を `pass` に替えると落ちることを確かめた。

## 3. 「Claude に選ばせる」

`claudeCorners` で、Claude の四隅（写真の下を手前とした順）を `BgCornersView.renamed(四隅, null, sideSent())` で名前を付け直してから使う。
右からなら写真の右上が TL、左からなら左下が TL。ボタンは横からのモードでも出したまま。

`renamed(four, from, to)` は `analyzer/static/corners-view.js` に置いた（4 つの値を、写真の上の場所はそのままに、別の撮り方での名前に並べ替える）。
Node のテストで使えるように `module.exports` も足した。

## 4. 写真の履歴

- `historyRecord` に `sideMode`・`sideFrom` を足した
- `startPhoto`: 写真に残したもの（`kept`）があればそれを使い、新しい写真は端末に覚えた既定（`storedSide()`）を使う。
  0.68.0 より前に残した写真には `sideMode` が無いので、普通のモードとして開く（そのころは普通のモードしか無かったため）。
  そのときの `sideFrom` は端末に覚えたもの
- 切り替えは、端末の既定（localStorage）と今の写真（state。履歴に残る）の両方を変える

## 5. 切り替えで手置きの隅を残す

`cornersAfresh` を `cornersAgain(was)` に替えた（`was` は切り替える前の `sideSent()`）。
- 送る向き（`sideSent()`）が変わらないときは何もしない（初めてオンにして、左右をまだ選んでいないときなど）
- 四隅が 4 つあり、手で置いた隅があるとき: 四隅と `cornersFixed` を `renamed(…, was, 今)` で付け直し、`findAgain()`（手置きの隅を `fixed` に渡して残りを探す）
- 手で置いた隅が無いとき: 今までどおり 4 つとも探し直す

## テスト

`analyzer/test_side.py` を 8 件から 15 件にした:
- 左の geometry（2）
- 写真ごとの記録と復元（文字列）
- `cornersAgain` の付け直しと `findAgain`、Claude の付け直し（文字列）
- `renamed` の値（Node）
- `sample.js` の `side`（Node）
- `/samples` の `side`
- `collected.valid` と `import_collected.clean`
- `evaluate.run` と `check_corners.measure` が truth の `side` で横からのモードを使うこと

壊すと落ちるか（そのたびに戻した）。どれも 1 件落ちた:
- `evaluate.py` で `side` を渡さない
- `check_corners.py` の分岐を外す
- `collected.valid` の確かめを外す
- `clean` で `side` を残さない
- `samples.py` の確かめを外す
- `sample.js` で `side` を入れない
- `renamed` の右と左を入れ替える
- （2 回目の報告の分に加えて）H の半回転を消す

| コマンド | 結果 |
|---|---|
| `uv run pytest analyzer/test_side.py -q` | 15 passed |
| `uv run pytest analyzer/test_collected.py -q` | 8 passed |
| `uv run pytest analyzer/test_pwa.py -q` | 25 passed |
| `uv run pytest analyzer/test_photo_view.py -q` | 12 passed |
| `uv run pytest analyzer/test_api.py -q` | 49 passed |
| `node --check`（app.js、corners-view.js） | 0 |
| `uvx ruff check --select F recognizer/ analyzer/` | 1 件。着手前からある `analyzer/test_api.py:361` の未使用 import で、触っていない |

## 普通のモードを変えていない根拠

今回の recognizer の変更は、`side` が無い truth では今までと同じ道を通る。`evaluate.run` は `side=None` を渡し（2 回目で `side=None` の `recognize` が HEAD と一致することは確かめた）、
`check_corners` は `if t.get("side")` の外、`valid`・`clean` は足しただけ。PWA は、横からのモードがオフなら `sideSent()` が null で、`renamed(…, null, null)` は並べ替えない。

## 残る懸念

- PWA はブラウザで操作していない（Claude の付け直し、履歴の復元、切り替えで手置きの隅を残す動き）
- 切り替えで残す隅は、写真の上の場所で付け直す。利用者が、前の向きとは合わない順で置いていた場合（普通のモードのまま、横からの順で置いたなど）は、付け直すと名前がずれる
- 手置きの隅があるときの探し直しは、見つからなければ付け直した四隅のまま（「見つからない」）。その中には前の向きで自動で見つけた隅も混じる
- 0.68.0 より前に残した写真は、端末の既定が横からでも、開き直すと普通のモードになる（判断が要るなら変える）
