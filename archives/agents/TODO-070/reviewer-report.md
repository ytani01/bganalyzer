# TODO-070 reviewer の報告

対象: `git diff`（ブランチ `claude/todo-070-photo-edit`、未コミット）。テストの実行と Playwright での実測はしていない（依頼どおり）。
数式の確かめだけ Node で行った（下の「問題ない観点」）。

## 要修正

### 1. TODO.md:99 — TODO-069 のチェックが入っている
- **何が起きるか:** TODO-069（上がった駒とキューブ）の「analyzer の版を上げる」に `[x]` が入った。TODO-069 はまだ実装されておらず
  （`board-view.js` の項目は `[ ]` のまま、PR #225 は項目を立てただけ）、この差分の版上げは TODO-070 のもの。
- **根拠:** `git show --stat ba4a67a`（TODO.md だけの変更）。~/.claude/CLAUDE.md「チェックボックスは実装できた時点で入れる」。
  TODO-069 に着手したとき、版を上げずに済ませてしまうおそれがある。範囲外の変更でもある。

## 検討

### 2. docs/PI_CHECKS.md:98, :100 — PI-047 に「範囲を囲む」が残っている
- **何が起きるか:** 108 行のスマホの行は直したが、同じ項目の「ここで確かめること」（98 行「範囲を囲んだときのもう一度の検出」）と
  「確かめ方」（100 行「`collected-sj1vrx.jpg` で「範囲を囲む」→ 四隅が盤に合うかを 1 回」）が旧画面のまま。
  Pi の Claude かユーザーが 100 行を読むと、無いボタンを探すことになる。96 行（確かめ済みの記録）はそのままでよい。

### 3. app.js:570（applyEdit）・photo.js turn() — 原寸の写真をそのまま canvas で回す（実害は未確認）
- **何が起きるか:** `BgPhoto.turn(state.photo.bitmap, …)` は原寸の写真から、回した外接矩形（切り抜けばその部分）の canvas を作る。
  iOS Safari の canvas の面積の上限は約 16.7M 画素とされる（未確認。端末では測っていない）。計算では、12MP（4032x3024）を
  15° 回して切り抜かないと 4677x3964 = 18.5M、24MP（5712x4284、最近の iPhone の既定）だと 90° 回すだけで 24.5M になり、上限を超える。
  そのとき `toBlob` は null を渡し、`jpeg()`（633 行）は reject しないので `new File([null])` が "null" の 4 バイトのファイルになり、
  `decode` の失敗として「画像を編集できませんでした: …」の分かりにくい文言で出る（history.js の `toBlob` は null を reject している）。
- **補足:** 以前は `uploadImage` が 2048 に縮めてから canvas に描いていたので、この上限に当たらなかった。
  縮めるかどうか（サーバーに送るのも 2048、履歴も `MAX_SIDE` なので原寸は要らない）は管理者の判断。

### 4. app.js:640-644（cornersForm）— 切り抜けば必ず「画像全体を crop」で送る（実害は未確認）
- **何が起きるか:** `trimmed` は矩形を引いたかどうかだけで決まる。端を少し落としただけの切り抜き（盤が画像の一部しか占めない）でも
  「盤が画像の大部分を占めてよい」として探す。`measure_cropped.py` が比べたのは、正解の四隅の外接矩形に 15% の余白を付けた切り抜きだけで、
  ゆるく切り抜いたときに `crop` を送る方が悪くならないかは測られていない。測り直しは依頼どおりしていない。境界線上の判断なので報告だけ。

### 5. app.js:135, :942 — 編集中に「前に読み取った盤面を開く」（hdr-reuse）で盤面へ行ける
- **何が起きるか:** 盤面を読み取ったあとの写真では、編集中もヘッダーの `hdr-reuse` が出ている（`s.step === "corners" && s.fromPhoto && s.board`）。
  押すと `state.edit` が残ったまま盤面の画面へ行き、戻る（`previousStep` は "corners"）と編集の表示のまま戻る。
  戻るボタン（写真の画面へ）でも `edit` は残るが、写真の画面から四隅へは `startPhoto` を通るので、そちらは消える。
  壊れはしない（「やめる」で戻れる）が、意図した挙動かは未確認。

### 6. app.js:570-576 / history.js `update` — 置き換えと、走っている四隅探しの persist が競合しうる（実害は未確認）
- **何が起きるか:** `PhotoHistory.update` は get と put を別のトランザクションで行う。「画像を編集」は走っている四隅探しを止めない
  （overlay を止めるだけで、要求は続く）。その答えが `replace` の get と put の間に届くと、`update()` → `persist()` の get が
  置き換え前のエントリーを読み、`replace` の put のあとに古い `image` ごと書き戻しうる。そのあと `startPhoto` の `persist(true)` は
  新しい写真の四隅・`trimmed` を古い画像に書くことになる。起きる窓は数 ms で、再現はしていない。

### 7. テスト — 90° 回したときの矩形の変換にテストが無い
- **何が起きるか:** app.js:946-953 の分数の変換はイベントハンドラーの中にあり、Node のテスト（test_photo_view.py は photo.js を
  `require` して試している）から呼べない。`check_pwa.py` も「矩形を引いてから 90° 回す」組み合わせは通していない。
  式は正しい（下の「問題ない観点」）が、壊しても落ちるテストが無い。photo.js に純粋な関数として置けば
  test_photo_view.py で試せる。`history.js` の `replace` も Node のテスト（test_pwa.py は純粋な関数だけ）では試していないが、
  IndexedDB が要るので今の作りに合わせれば Playwright 側でよい。

## 好みの範囲

### 8. app.js:42 — `edit` の行のコメントが 194 文字
- 変更前の app.js の最長は 157 文字。行長の決まりは CLAUDE.md に無いので好みの範囲。

### 9. index.html:101-122 — `#corner-tools` の中身が字下げされていない
- 包む `<div>` を足したが、中の行は元の字下げのまま。

## 作り込みすぎ

- `app.js:946-953: shrink:` 「左に 90°」「右に 90°」が同じ形のハンドラー 2 つ。左は右を 3 回と同じなので、
  `const quarter = (r) => [1 - r[3], r[0], 1 - r[1], r[2]]` を右に使い、左は 3 回かけるか、`(dir)` を取る 1 つの関数にまとめる。約 -3 行。
- ほかは無駄な抽象は無い（`copies` は `add` と `replace` の 2 か所で使う、`editPreview` のキャッシュはスライダーの動きに要る）。

net: -3 lines possible.

## 問題ない観点（1 行ずつ）

- 90° の矩形の変換（app.js:946-953）と `turn()` の座標系: 一致。Node で、元の画像の点を deg と deg±90 で回した外接矩形の分数に写し、
  右は (u, v) → (1 − v, u)、左は (u, v) → (v, 1 − u) になることを、細かい角度 0・17・−33・102° で確かめた（誤差 1e-9 以下）。
  `ctx.rotate` の正の向き（画面で時計回り）とも合う。
- applyEdit → startPhoto の引き継ぎ: `corners: null` で探し直し、`cornersMoved`・`cornersFixed`・`geometry`・`edit` はリセット、
  `board`・`read`・設定は残り、`result` は `setResult(null)` で消える。README の記述（読み取った盤面や設定はそのまま残る）と合う。
- `historyScale`: `replace` が返す縮尺を渡し、再オープンでは 1。`sampleOf` は置き換えた `e.image` と `historyScale` を使うので、
  「Pi に残す」・書き出しも編集後の画像と四隅で揃う。
- `trimmed` の再オープン: `historyRecord` に入り、`openHistory` → `startPhoto` で `kept.trimmed` から戻り、`guessCorners`・`findAgain` の
  `cornersForm` で `crop` が付く。古いエントリー（`trimmed` 無し）は false。
- `crop` の画素: 送る画像（縮めたときは `scaledCanvas` と同じ `Math.round(iw * scale)`）の全体で、`measure_cropped.py` と同じ `(0, 0, w, h)`。
- 探す世代: 編集の確定は `startPhoto` → `guessCorners` で `search` を進め、前の写真の答えは `state.photo.file !== file` で捨てる。
  編集を始めると `stopOverlay("corners")` で overlay を止め、編集中は corners が空・`recognize` 無効・`find-again` と `corner-reset` は隠れる。
- 編集中の resize: `editPreview` は角度が変わったときだけ回し直し、`draw` は preview の大きさで座標を取るので、矩形は分数のまま保たれる。
- バージョン: analyzer 0.44.0 → 0.45.0（機能の変更）、`APP_VERSION`・`sw.js` の `CACHE` も揃っている。recognizer は変えていない。
- 旧機能の残り: `rg -n -e crop -e trimming -e 範囲を -e crop-start -e crop-clear analyzer tools docs README.md` で、PWA と tools に
  `crop-start`・`crop-clear`・`state.crop` は残っていない（残りは上の 2 の PI_CHECKS と、API の `crop` とそのテスト）。
- analyzer/README.md: 画面の手順・途中経過の表示・`/find-corners` の `crop` の説明が実装と合う。
- コメント: 新しいコメントは理由を書いている（`cornersForm`、`applyEdit`、90° の矩形）。
