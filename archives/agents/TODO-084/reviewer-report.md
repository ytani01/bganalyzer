# TODO-084 reviewer 報告

対象: `git diff main...HEAD`（claude/todo-084-fix-corners-impl、88c6141）。コードの読み合わせで見た。テストと読みの測定は流していない。

要修正: 0 件。

## 問題が無かった観点（1 行ずつ）

- board.py の既定（`keep_corners=False`）: 前と同じ処理になる。`tips = []` は、ループが必ず 2 回回って `refine_tips` の戻り値で上書きされ、そのあと `find_tips` でまた上書きされるので、消しても値は変わらない
- board.py の `keep_corners=True`: H は `snap_h(homography(src_pts, corners))` で、`refine` の H0 と同じ作り方に snap を足したもの。`fit_columns` の `reach` は既定 1.2 で、既定の経路の 1 回目と同じ。`lay` は `snap_layout` の幅のまま（バーの幅を測り直さない）で、要件（列だけ合わせる）に合う。`quality=0.0` は `info["edge_quality"]` に入るだけで、analyzer・tools・recognizer のどこからも読まれていない（`rg edge_quality`）
- app.py: `keep_corners` を `Form(False)` で受けて `recognize` に渡している。既定は前と同じ
- テスト: 指定を無視すると fit が `edges`×2・`triangles`×2 の 4 回になり、`[("corners", 1)]` の assert で落ちる。app.py が渡し忘れても同じく落ちる
- 版: analyzer 0.49.0 → 0.50.0、recognizer 0.22.3 → 0.23.0、`APP_VERSION` も 0.50.0。機能の追加なので minor を上げるのは CLAUDE.md の「バージョン」どおり
- JS の状態: 新しい写真（`kept=null` → false）、履歴から開く（`kept.keepCorners`。古い記録は `undefined` → false）、画像の編集（false）、Claude の四隅（false）、送信（true のときだけ `keep_corners=true`）、チェックボックスの表示（`part` の初回描画で入る）。漏れは無い。`tools/pi_ui_check.py` は `BgApp.update` で四隅を置くので `keepCorners` は false のままで、今までどおり既定の読みで動く
- PI_CHECKS.md: 「残っている項目」「次の番号 PI-051」「新しい番号ほど上」は合っている。決着 48 件は `archives/pi/PI-*.md` の 48 本と一致。`BgApp.state.geometry.corners` は app.js で写真の画素へ戻している（`scaleGeometry`）ので `state.corners` と比べられる
- 範囲: 指示に無い変更は無い（index.html の「ざっくりで大丈夫です」をチェックボックスの説明へ移したのは、この機能の説明として妥当）
- 作り込みすぎ: なし

## 検討

1. `analyzer/static/app.js:176`（と `analyzer/static/corners-view.js:145`）
   何が: `onChange` は pointerdown の時点でも呼ばれる。点を動かさずに触っただけ、また四隅をやり直したあとに 4 つタップして置いたときも `keepCorners` が入る。
   なぜ: 要件は「点を手で動かしたら自動で入る」。タップで置いた点は「ざっくり」のことが多く、index.html の説明（「ざっくり合わせたときは外してください」）と逆の向きに働く。`cornersMoved` も前から同じ契機で立つので、それに揃えたとも読める。
   判断が要る点: タップで置いた・触っただけ、のときも入れてよいか。実害は未確認。

2. `analyzer/static/app.js:753`（`findAgain`）
   何が: 1 つ動かして `keepCorners` が入ったあとに「もう一度検出」を押すと、残り 3 つが検出した四隅に置き換わるが、チェックは入ったまま。検出した 3 つも合わせ直さずに読まれる。
   なぜ: 外す場面に挙がっているのは「新しい写真・画像の編集・Claude の四隅」で、「もう一度検出」は挙がっていない。動かした 1 つは残るので入れたままにする理由もある。
   判断が要る点: 「もう一度検出」で見つかったとき外すか。実害は未確認。

3. 文書の取り残し（fit が 4 回という記述に `keep_corners` の例外が無い）
   - `analyzer/README.md:87-88`「四隅の合わせ直し 4 回（枠の線で 2 回、三角形の並びで 2 回…）」（画面の読み取りの段階の説明）
   - `recognizer/README.md:540`「`fit`（四隅の合わせ直し 1 回ごと。枠の線で 2 回、三角形の並びで 2 回）」
   - `analyzer/static/scan.js:68` のコメント「枠の線で 2 回、三角形の並びで 2 回」
   - `recognizer/board.py:84` の docstring「"fit" four times」（直前の `keep_corners:` の行で補ってはいる）
   なぜ: 差分では `analyzer/README.md:217` の API の節だけ直してある。同じ主張がほかに 3〜4 か所残っている。

4. `recognizer/README.md:13`「ざっくりで構いません（盤の縁と三角形の先端で自動補正します）」
   なぜ: `--keep-corners` では補正しない。直後の行に `--keep-corners` の説明はあるが、この文には条件が付いていない。

5. `TODO.md` の TODO-084
   何が: 「（チェックの状態を覚えるかは着手時に決める）」を消したが、決めたこと（写真の履歴に保存し、開き直すと戻る）が書かれていない。
   なぜ: 実装は `historyRecord` に `keepCorners` を入れて覚えている。決着のファイルへ移すときに理由が辿れない。

6. `recognizer/README.md:513-526` の表の値（photo6 18→14 など）
   未確認。測り直していない（依頼で外した範囲。verifier が測るなら代表 1 枚で足りる）。

## 好みの範囲

1. `analyzer/test_photo_view.py:93-94` 新しいテストの後ろの空行が 1 行で、ほかの関数の間（2 行）と揃っていない（PEP 8 の E302）。lint は CI に無い（`rg ruff|flake8 pyproject.toml .github` で該当なし）。
