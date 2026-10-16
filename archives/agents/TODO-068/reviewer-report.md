# TODO-068 reviewer の報告

対象: `git diff`（作業ツリー。recognizer/corners.py・check_corners.py・analyzer/・docs）。
コードは直していない。実測に使ったスクリプトはスクラッチ（リポジトリの外）に置いた。

## 要修正

### 1. `analyzer/README.md:163-169`: `POST /find-corners` の説明に `fixed`・`crop` が無い

- 何が問題か: API にフィールドが 2 つ増えたのに、API の節は「フィールド `image`」のままで、形の違う値で 422 になることも書いていない。
  「PWA は写真を読み込んだ直後に…送り、結果を四隅の初期値にする」も、もう一度検出で送ることが抜けている
- 根拠: `analyzer/app.py:133-134,141-149`（実装）と `analyzer/README.md:163-169` を読んで突き合わせた。`rg -n "fixed|crop" analyzer/README.md` は 0 件

### 2. `analyzer/README.md:38-39`・`:72-74`: 使い方と途中経過の説明が新しい操作に追いついていない

- 何が問題か: 使い方の 2. に「範囲を囲む」「範囲を戻す」「もう一度検出」が無い。途中経過の節は「四隅探し（写真を読み込んだ直後）: 写真全体に走査線」で、
  もう一度検出のとき（囲んだ範囲から始まる）を書いていない
- 根拠: 上の 2 か所を読んだ。`rg -n "範囲を囲む|もう一度検出" --glob '!archives/**'` は app.js・index.html・PI_CHECKS.md だけに当たる
- 同じ観点で好みの範囲: `README.md:83` の `analyzer/static/` の行（「四隅の初期値をドラッグで調整」）と `docs/HANDOVER.md:79` の「四隅の初期値」も、もう一度検出に触れていない

## 検討

### 3. `analyzer/static/app.js:654`（と `:355`・`:485`）: もう一度検出の最中に履歴へ "finding" が残ると、開き直したとき直した四隅が捨てられる

- 何が起きるか: `findAgain` は `update({ cornerGuess: "finding" })` をし、`update` のたびに `persist()` が `cornerGuess` を履歴に書く（`:355`、`:96`）。
  この間に別の写真へ移る・アプリを離れる（`visibilitychange` でも `persist`。`:985`）と、履歴には「ユーザーが直した四隅 + "finding"」が残る。
  開き直すと `startPhoto` が `kept.cornerGuess === "finding"` を見て四隅を写真の内側の長方形に戻し、最初の自動検出からやり直す（`:485-489`）
- 根拠: コードを読んだだけ。ブラウザでは試していない（**実害は未確認**）
- 補足: 最初の自動検出の最中に隅を動かして離れたときも同じことが起きるので、前からある。もう一度検出は「直した四隅の上で」走るので、当たる場面が増える

### 4. `analyzer/test_api.py:233-256`: `TRIMMED` を外してもテストが落ちない。`crop` のときの途中経過の座標の戻しもテストが無い

- 実測: corners.py を書き換えた写しで、`test_corners_keep_the_fixed_ones_and_look_in_the_trimmed_part` と同じ 4 つの判定を流した（○ = 通る）

  | 壊し方 | fixed 2 つ | 4 つ固定 | 中央に固定→None | sj1vrx を crop |
  |---|---|---|---|---|
  | `_move_in` のあとの `pin` を外す | 落ちる | ○ | ○ | ○ |
  | `NEAR` の条件を外す | 落ちる | ○ | 落ちる | ○ |
  | 候補の `pin(q)` を外す | 落ちる | ○ | ○ | ○ |
  | `TRIMMED` をやめ既定の大きさにする | ○ | ○ | ○ | ○ |

  `TRIMMED` は README で screen2 を 22.8% → 1.6% にしたと書いている部分だが、どの判定も落ちない
- `find_corners` の `emit` の `+ at`（`corners.py:375`）は、`crop` と `stream` を一緒に渡すテストが無いので、外しても落ちない（読んで確認。実行はしていない）

### 5. `recognizer/corners.py:313`・`recognizer/README.md:237`: `NEAR` の基準が、囲んだときは写真ではなく囲んだ範囲の長辺になる

- 何が起きるか: `guess` の `h, w` は切り出して縮めた画像の大きさなので、`crop` があると 5% は「囲んだ範囲の長辺の 5%」。README は「写真の長辺の 5%」、定数のコメントは
  "against the photo's side" と書いている。挙動として悪いかは判断しない（文書と合っていないことだけの報告）
- 根拠: `corners.py:366-381` で `small` は `img[y0:y1, x0:x1]` を縮めたもの

### 6. `analyzer/app.py:146`: `crop` に `nan`・`inf` を送ると 500

- 実測（TestClient、screen1）: `crop=nan,0,100,100`・`inf,0,100,100`・`0,0,1e400,100` が 500（`find_corners` の `int(crop[...])` で ValueError / OverflowError）。
  `fixed` の `NaN`・`Infinity` は 200 で `corners: null`。PWA からは送らないので、**実害は未確認**
- 揃い方: `/analyze-photo` の `corners` も `float()` で受けて有限かは見ていないので、扱いは今のものと揃っている
- ついでに見えたこと（好みの範囲）: `fixed=["12", null, null, null]` は文字列が 1 文字ずつ数になり `[1.0, 2.0]` として通る

### 7. `TODO.md:102-104`: 実装済みの項目にチェックが入っていない

- 何が問題か: corners.py と API、PWA、版と `cpu_reference.json` と PI_CHECKS はどれも差分にあるが、3 つとも `- [ ]` のまま
- 根拠: `~/.claude/CLAUDE.md`「`TODO.md` のチェックボックスは実装できた時点で入れる（確認の担当に回す前）」

### 8. `docs/PI_CHECKS.md:95`: `PR #?` が埋まっていない

- PR を作るときに番号を入れる必要がある

## 好みの範囲

- `recognizer/corners.py:313`: 内側のリスト内包の `for i in keep` が、外のループの `i`（`for i in range(len(vl))`）と同じ名前。Python 3 では漏れないので動きは正しいが、読むときに紛らわしい
- `recognizer/corners.py:368`: `crop` が 16 px 未満だと、4 つとも固定していても `None` を返す（docstring は「4 つとも与えるとそのまま返る」）。PWA から届く大きさではまず起きない

## 問題の無かった観点

- **何も渡さないときの答え**: main の corners.py と今の corners.py で、56 サンプル × 原寸と `shrink_like_app` の 2 通り = 112 回、`find_corners` の答えと `progress` の全段の中身を比べて、違いは 0 件。
  `looked`（重複の除き方）が既定の流れで候補を落とした回数も、`shrink_like_app` の 56 枚で 0 件。`cpu_reference.json` の差分も meta だけ
- **float の処理**: 足したのは `exact.norm`、`np.round`、要素ごとの四則演算、`int()` だけ。CLAUDE.md の「精度の確認」で禁じている OpenCV の float の処理や `linalg` などは入っていない（`check_corners.py` の `np.min` は測る道具の中）
- **`pin` の流れ**: `NEAR` で捨てる → `pin` → 大きさの条件 → `looked`、`_move_in` のあとにも `pin`。`crop` の切り出し・`+ at` での戻し・4 つ固定のときに `at` を足さないこと、いずれも正しい
- **API**: 受け取りと 422 の扱いは `/analyze-photo` の `corners` と同じ書き方。`fixed=""`・`"null"`・`[null×4]`・`crop=""` は送らないときと同じ答え（実測）
- **PWA**: 固定の印（ドラッグとタップで付く、「四隅をやり直す」と新しい写真で消える、囲んだ範囲の外の隅は `onTrim` で外れる。`state.corners[k]` が無い隅は印も付かないので `inside` が undefined を受けることは無い）、
  拡大（`draw` の切り出し、`toImage` の範囲、`toCanvas` を使う scan.js とルーペがそのまま付いてくる）、結果の当て方（固定していない隅だけ置き換え、見つからないとき、途中で動かしたら捨てる、`search` の番号で古い検出を捨てる）は依頼どおり。
  `crop-clear` の `hidden` は `style.css:233` の `[hidden] { display: none !important; }` で効く
- **版**: analyzer 0.44.0 と `APP_VERSION`、`sw.js` の `CACHE` v52、recognizer 0.22.0。いずれも CLAUDE.md の「バージョン」どおり（機能の追加なので 2 つ目の数を上げる）
- **範囲**: 依頼に無い変更は無い
- **コメント**: なぜを書いている（`NEAR` で捨てる理由は README、`onTrim` の外す理由はコメント）

## 作り込みすぎ

作り込みすぎ: なし（`looked` は固定した隅で同じ四角形が上位を埋めないために要る。API の検証も `/analyze-photo` と同じ量）
