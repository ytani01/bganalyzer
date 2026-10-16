# TODO-068 implementer への依頼: `/find-corners` と PWA の四隅の画面

## 目的

四隅の画面で「検出 → ユーザーが直す → もう一度検出」を繰り返せるようにする。
ユーザーが動かした隅はそのまま残し、ユーザーが囲んだ範囲（トリミング）の中だけを探す。

## 済んでいること（main）

`recognizer/corners.py` の `find_corners(img, progress=None, fixed=None, crop=None)`（作業ツリーにある。コミット前）:

- `fixed`: TL, TR, BR, BL の 4 つ。それぞれ `[x, y]`（画像の px）か `None`。与えた隅はそのまま返り、残りだけを探す。4 つとも与えるとそのまま返る
- `crop`: `(x0, y0, x1, y1)`（画像の px）。この範囲の中だけを探す。返る四隅と `progress` の座標は画像全体の px
- 見つからなければ `None`（固定した隅と合う候補が無いときも `None`）
- テストは `analyzer/test_api.py` の `test_corners_keep_the_fixed_ones_and_look_in_the_trimmed_part`

## やること

### API（`analyzer/app.py` の `/find-corners`）

- Form に任意の 2 つを足す: `fixed`（JSON の文字列。長さ 4 の配列で、各要素は `[x, y]` か `null`。送った画像の px）、
  `crop`（`"x0,y0,x1,y1"`。送った画像の px）。形が違えば 422（`/analyze-photo` の `corners` の扱いに合わせる）
- `find_corners(img, progress, fixed=..., crop=...)` に渡す。`stream` のときもそうでないときも
- `test_api_find_corners` に、`fixed`・`crop` を渡して通ること、形の違う値で 422 になることを足す

### PWA（`analyzer/static/`）

- **隅ごとに「ユーザーが置いた」を覚える**（例: `state.cornersFixed = [false, false, false, false]`）。ドラッグした隅と、タップで置いた隅を true にする。
  `corners-view.js` の `onChange` は今、どの隅が動いたかを渡していないので、渡すようにする。「四隅をやり直す」と新しい写真で全部 false に戻す
- **トリミング**: 四隅の画面のボタンで「範囲を囲む」モードに入り、写真の上を斜めにドラッグして矩形を決める（囲んでいる間は矩形を描く）。
  指を離したら、その範囲を `state.crop`（写真の px）にし、**写真の表示をその範囲に拡大し**、続けて「もう一度検出」を走らせる。
  小さすぎる矩形（どちらかの辺が表示で 40 css px 未満など）は無視する。範囲を決めたら「範囲を戻す」ボタンで写真全体の表示に戻せる（`crop` を null に）
  - 表示の拡大は `corners-view.js` の `draw`・`toImage`（範囲の外に出ないように）で行う。scan.js の重ね描きと拡大鏡（loupe）は `toCanvas` を使っているので、そのまま拡大に付いてくるはず
- **もう一度検出**: ボタンを置く。今の `guessCorners` と同じく `/find-corners` を `postStages` で呼び、途中経過（scan.js）を見せる。
  送る画像は今と同じ `uploadImage()` のもの。`fixed`（固定した隅だけ。他は null）と `crop` を送る画像の px（`scale` を掛ける）にして送る。
  scan.js の始めの四角形は、`crop` があればその範囲、無ければ写真全体
  - 見つかったら、固定していない隅だけを置き換える（固定した隅はサーバーからもそのまま返るが、クライアントでも上書きしない）
  - 見つからなければ: `crop` があれば固定していない隅を範囲の四隅に置く、無ければ四隅はそのまま。どちらも説明文で「見つかりませんでした」と伝える
  - 検出の途中にユーザーが隅を動かしたら、今の `guessCorners` と同じく結果は捨てる
- 最初の自動検出（写真を選んだとき）は今のまま
- 説明文（`corner-help`）と、トリミングのモード中の説明を足す。ボタンの文言はこの依頼の語（「範囲を囲む」「範囲を戻す」「もう一度検出」）でよい
- `history.js` など、写真ごとに保存・復元している状態があれば、`crop` と固定の印をどう扱うかは「新しい写真で消える」だけ守ればよい（復元はしなくてよい）

### 版

- analyzer の版を 0.43.0 → 0.44.0（`analyzer/app.py` の `__version__` と `analyzer/static/app.js` の `APP_VERSION`）。`sw.js` の `CACHE` も上げる
- recognizer の版・`cpu_reference.json`・docs は main がやる。触らない

## 保つもの

- 写真を選んだときの最初の自動検出・途中経過の表示・「四隅をやり直す」・読み取り（`/analyze-photo`）の動きは変えない
- `/find-corners` に `fixed`・`crop` を送らなければ、答えは今と同じ
- 座標の約束: 四隅は TL, TR, BR, BL、写真（bitmap）の px で持ち、送るときに `scale` を掛ける

## やらないこと

- `recognizer/` は触らない（corners.py の中身の変更が要ると思ったら、直さずに報告する）
- 四隅の検出の精度の測り直しはしない

## 完了条件と確かめ方

- `uv run pytest analyzer` が通る
- PWA を実際に動かして、代表 1 枚（`samples/collected-sj1vrx.jpg`。盤が小さく、最初の検出では見つからない）で
  「範囲を囲む → 自動でもう一度検出 → 四隅が盤に合う」と、「隅を 1 つ動かす → もう一度検出 → その隅は動かず残りが置き直される」を確かめる。
  手段は `tools/ui_snapshot.py` か Playwright（`uv run -q --no-project --with playwright python ...`）。画面は 390x844 で 1 回ずつ
- 報告は `archives/agents/TODO-068/implementer-report.md` に、変更点・確かめた結果（測った値・画面の様子）・残る懸念だけ書く。
  返事は「終わったか・報告ファイルのパス・判断が要る点」だけにする
