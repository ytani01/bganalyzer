# TODO-120 実装の報告（implementer、2 回目、2026-10-17）

試作の手法は変えずにアプリへ出した。6 枚での数は試作と同じ（正解の四隅で 22・18・14・23・14・14、左右反転で 21・19・15・23・13・13）。

## 変えたファイル

### recognizer（版 0.23.2 → 0.24.0、`recognizer/board.py:52`）

- `recognizer/side.py`
  - `_guess(small, emit, fixed, least)`（side.py:60）: `corners.guess` と同じ呼ばれ方にした。途中経過は `uprights`（長い辺）→ `edges`（両端）→ `candidates`（上位 `corners.REFINE` 個）。
    `fixed` は `corners.guess` と同じく、ずれが `NEAR` を超える候補を捨て、残りは置かれた隅で上書きする（`_move_in` のあとも上書き）。`least` は使わない（docstring に書いた）
  - `find_corners_side(img, side, progress=None, fixed=None, crop=None)`（side.py:134）: `corners.find_corners(..., search=_guess)` を呼び、四隅の順を side に合わせる。
    `fixed` は渡すときに「右から」の順に直す。途中経過の `corners` 段も順を直す。縮小・`crop`・4 つとも固定のときの扱いは `find_corners` のまま
  - `read_side(img, corners, side, emit, debug)`（side.py:286）: `board.recognize` 用の部品にした。返すのは `(H, lay, tips, circles, pitch, runs, bar, cc, board)` で、
    すべて手前の人の向き（`H` はそこから写真へ）。左のときは、数える前に図・列・円・先端を盤の中心のまわりに半回転させる。
    `fit`（`by="side"`、1 回）と `tips` を emit する。ポイントの数を返していた試作の `read_side` はなくした
- `recognizer/board.py`
  - `recognize(..., side=None)`（board.py:78）: `side` があれば `side.read_side` の結果を `_finish` に渡す。無ければ今までどおり
  - `_finish(...)`（board.py:177）: 今まで `recognize` の後半にあった処理（ホームの推測、`to_position`、geometry、ダイス、キューブ、警告）を、行の中身は変えずに関数へ移した。
    `side` のときは斜めの警告を出さず、`info["side"]` を入れる。普通のモードの `save_debug` は、数え終わったところへ移した（デバッグ画像を書く順が変わるだけ）
- `recognizer/corners.py:355-385`: `find_corners` に `search=None` を足した（無ければ `guess`）
- `recognizer/README.md`: 「横から撮った写真（`side.py`、TODO-120、recognizer 0.24.0）」の節（向き、手法、6 枚の表、苦手なもの）と、ファイルの一覧に `side.py`

### analyzer（版 0.67.0 → 0.68.0。`analyzer/app.py:34`、`analyzer/static/app.js:14`）

- `analyzer/app.py`
  - `/find-corners`（app.py:138）: フォームに `side` を足した。`right`/`left` なら `find_corners_side`、空か無しなら今までどおり。ほかの値は 422
  - `/analyze-photo`（app.py:170 前後）: フォームに `side` を足し、`recognize(..., side=side)` に渡す
  - `_side()`（app.py:216 前後）: 値の確かめ
- `analyzer/static/index.html`: 四隅の画面の「四隅を固定する」の横に「横から撮った」のチェックボックス（`#side-mode`）。その下に「撮った位置」の行（`#side-from-row`）。
  中身は `seg`（`data-name="sideFrom"`、右から／左から）と、まだ選んでいないときだけ出る問いかけ（`#side-ask`）
- `analyzer/static/app.js`
  - state に `sideMode`・`sideFrom`。localStorage の `sideMode`（on/off）と `sideFrom`（right/left、未選択は ""）から読む
  - `setSideMode`: 覚えてから、オフにしたとき、または位置がもう選んであるときに、四隅を探し直す（`cornersAfresh`）。初めてオンにしたときは位置を選ぶまで待つ
  - `setSideFrom`: 覚え、オンなら探し直す（位置はオンの間いつでも選び直せる）
  - `cornersAfresh`: 四隅を初期の長方形に戻し、固定した隅・「四隅を固定する」も外して `guessCorners` を呼ぶ（モードが変わると、前の四隅は別の向きの約束で置いたものになるため）
  - `cornersForm`（`/find-corners` の「もう一度検出」でも使う）と `recognize`（`/analyze-photo`）で、オンかつ位置が選んであるときだけ `side` を送る
- `analyzer/README.md`: PWA の使い方と、`/find-corners`・`/analyze-photo` の `side`

### テストと文書

- `analyzer/test_side.py`（新規）: photo5 を撮ったままの向きに回し、アプリと同じ長辺 2048 に縮めて使う
  - 右からの四隅の誤差が 6% 未満。左からの四隅が、右からの四隅を `[2, 3, 0, 1]` に入れ替えたものと一致する
  - `fixed` の隅がそのまま返る（右から、左から）
  - `recognize(side="right")` が 20/24 以上。`info["side"]` があり、警告は出ない。geometry の四隅が渡した四隅に重なる。
    同じ写真を四隅の名前を入れ替えて `side="left"` で読むと、点が 12 ずれた並びになる（盤の半回転）
  - API: `/find-corners` が `side` を受け、段階の順と結果が `find_corners_side` と同じになる。不正な値は 422。`/analyze-photo` が `side` をそのまま `recognize` へ渡す（空・無しは None）。不正な値は 422
  - PWA: チェックボックスと左右の選択が四隅の画面にあること、localStorage の読み書き、問いかけを隠す条件、探し直す条件、`side` を 2 か所で送ること（今の `test_pwa.py` と同じく文字列で確かめる）
- `README.md`（処理の流れの下）、`docs/corners.md`（「横から撮った写真」の節）
- `archives/agents/TODO-120/measure_side.py`: 読み取りを `board.recognize(side=...)` 経由にした

## テストの結果

| コマンド | 結果 |
|---|---|
| `uv run pytest analyzer/test_side.py -q` | 8 passed |
| `uv run pytest analyzer/test_photo_view.py -q` | 12 passed |
| `uv run pytest analyzer/test_pwa.py -q` | 25 passed |
| `uv run pytest analyzer/test_api.py -q` | 49 passed |
| `uv run python archives/agents/TODO-120/measure_side.py --no-current <6 枚>`（と `--mirror`） | 0。数は試作と同じ |
| `uvx ruff check --select F`（変えた .py） | 0 |
| `node --check analyzer/static/app.js` | 0 |

壊すと落ちるかを確かめた（そのたびに戻した）:
- 左の四隅の順を `[1, 0, 3, 2]` にする → 3 件落ちる
- 左で円を半回転させない → 1 件落ちる
- `/analyze-photo` が `side` を渡さない → 3 件落ちる
- `/find-corners` が `side` を無視する → 1 件落ちる

## 普通のモードを変えていない根拠

- HEAD の `recognizer/` を取り出し、`samples/` の 6 枚（2aunci・gka56t・wkky1g・commons-rollup-oblique・photo3・synth-cube-photo4-16）で `recognize` を比べた。
  返す盤面、info の全部、progress の全段階が一致した
- `find_corners` は、HEAD とこの版で 4 枚（2aunci・gka56t・w8eaks・commons-diagram-prime）を比べた。答えも途中経過も一致した
- API の `side` は、空か無しなら `None` で、`find_corners`・`recognize` を今までどおりに呼ぶ

## 判断したこと（確認してほしい点）

- 横からのモードでは斜めの警告（「真上から撮り直すと…」）を出さないことにした。横から撮ったと利用者が言っているので、撮り直しを勧めても役に立たないため
- `side` と `keep_corners`（四隅を固定する）を一緒に送ると、`keep_corners` は効かない（横からの読み取りは、もとから四隅を合わせ直さない）
- モードや左右を切り替えると、手で置いた四隅も捨てて探し直す
- 横からの `/find-corners` は、普通のモードと違って、点数が低くても何かを返す（`MIN_SCORE` で切らない。試作のまま）

## 残る懸念

- PWA は、文字列のテストと `node --check` で確かめただけで、ブラウザで操作して試していない（live_view での確認は TODO.md の `- [ ] ローカル:` の行）
- 途中経過の段の順が `uprights` → `edges` になる。scan.js は段の名前で描くので描けるはずだが、見た目は確かめていない
- 手法の精度と苦手なもの（バーの陰の列、四隅の点数、CPU による違い）は 1 回目の報告のまま
- テストの写真（photo5 を回したもの）は、手法を試した 6 枚の 1 枚でもある。ほかの写真での当たり具合は保証しない
