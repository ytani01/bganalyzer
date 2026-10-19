# TODO-159 implementer 報告

## 変更点
- `analyzer/static/index.html:168-185` `#sheet-cube`: 「中央・白・黒」の seg、`#cube-value`（select）、`#cube-offered`（チェック）をやめ、
  - 数の 1 列 `#cube-values`（`data-name="cubeValue"`: 中央・2・4・8・16・32・64）
  - `#cube-side`（中央のとき隠す）に 2 つの seg: `cubeHold`（白側に置く・黒側に置く）、`cubeDouble`（白に対してダブル・黒に対してダブル）
  - `#cube-note`・`#cube-help` はそのまま
- `analyzer/static/cube.js`: `buttons(cube)`（cube → 押されて見えるボタン。`{number, hold, double}`）、`numberPatch(cube, v)`（数の列を押したときの cube の変更）を足してエクスポート
  - 中央から数 → `{at: "white", value, offered: true}`（以前の「白」ボタンの既定と同じ。白に対してダブルが選ばれた状態で 4 つの選択肢が出る）。片側にあるときは `{value}` だけ（置き方はそのまま）。「中央」→ `{at: "centre"}`
- `analyzer/static/app.js`: `SEGMENTS` に `cubeValue`・`cubeHold`・`cubeDouble`（`setCube` を通すので、クロフォードを外す・中央に戻す扱いは TODO-153 のまま）。seg の「押されている」表示を `BgCube.buttons` で出す。select・チェックの読み書きと `Option` の追加を削除
  - `choseInSheet`: 数のボタン（中央以外）ではシートを閉じない（選択肢が続くため）。それ以外の選択は今までどおり閉じる
- `analyzer/static/style.css:304-307`: 旧 `#cube-side label/select` を、`#cube-values`（余白と「中央」の幅）と `#cube-side`（縦に並べる）に置き換え
- `analyzer/README.md:81-86`: キューブの設定の説明と、「ダブルされたところ」のチェックの言い方を「…に対してダブル」「…側に置く」に直した
- `analyzer/test_pwa.py` に `test_cube_settings_buttons` を追加（`buttons`・`numberPatch` の写し方、html の seg の名前、旧 id が無いこと、`choseInSheet` の例外、`cubeHold`／`cubeDouble` の写し方）
- `tools/ui_snapshot.py`: 旧 `#cube-value`・`#cube-offered`・`cubeAt` を使っていた操作と `cube` の記録を、新しい seg 名に直した（直さないと動かないため）
- analyzer 0.88.2 → 0.89.0（`analyzer/app.py`、`analyzer/static/app.js` の `APP_VERSION`）。`TODO.md` の実装 2 項目にチェック

## 自分で確かめたこと
- `uv run pytest analyzer/test_pwa.py`: 33 passed
- 壊すと落ちるか: `numberPatch` の中央からの `offered: true` を `false` に変えると `test_cube_settings_buttons` が落ちた（戻した）
- 画面（worktree のサーバー 8767 番、live_view のブラウザ、390×844）で、サンプル collected-app-grey-shot を盤面まで読み、設定シートを開いて押した:
  - 中央 → 8（シートは開いたまま、`{white, 8, offered: true}`、4 つの選択肢が出る、`cubeDouble:white` が押された表示、ヘルプ「…のテイク／パスを判定します」）
  - 黒側に置く（`{black, 8, offered: false}`、シートが閉じる、ヘルプ無し）、4 に変える（置き方はそのまま `offered: false`）、黒に対してダブル（`offered: true`）、中央（`{at: centre}`、選択肢が隠れる）、中央から 2（`{white, 2, offered: true}`）
  - ページのエラー 0 件。最初は数を押すとシートが閉じていた（`choseInSheet`）ので上記の例外を足した
  - 「中央」が 2 行に折れていたので `#cube-values` の幅を直し、画像で 1 行に収まることを見た
- 盤のキューブの描画・タップ、クロフォード、ダブル中のダイスの扱いのコードは触っていない

## 判断が要る点
- 中央から数を押したときの置き方は「白に対してダブル」にした（旧 UI で「白」を押したときの既定と同じ）。選択肢を何も選んでいない状態は作れない（`state.cube` は必ず 4 つのうち 1 つ）ため。別の既定がよければ `numberPatch` だけ直せばよい
- 「中央」から数を押すと、クロフォードのゲームの設定は外れる（`setCube` が `at !== "centre"` のとき外す。TODO-153 のとおり）。画面では確かめていない（既存のテストの範囲）
- ラベルの「白」「黒」は盤の色に合わせて入れ替わる（`.nm-white`・`.nm-black`）ので、並びの先頭が「黒」になることがある（`bottomColour` による既存の動作）

## 残る懸念
- 結果の画面（`step === "outcome"`）の設定シートは見ていない（同じ HTML と `choseInSheet` を通る）
- worktree では `analyzer/test_api.py::test_version_reports_both_parts_and_commit` が `.git` がファイルのため落ちる（TODO-157・158 と同じ。範囲外）
- `docs/raspi.md:129` の「ダブルされたところ」という言い方は、Pi の確認の説明なので直していない

## 追記: レビューの指摘を直した
1. 中央から数を押したときの既定（`analyzer/static/cube.js` `numberPatch(cube, v, onRoll, dice)`）: 置く側を `other(onRoll)`（次に振る人の相手側。`fromRead` と同じ）にし、`offered` は「ダイスが無ければ true（…に対してダブル）、あれば false（…側に置く）」にした。`app.js` は `BgCube.numberPatch(state.cube, v, state.onRoll, rolled())` で呼ぶ。`request` に通すと `on_roll` は元の次に振る人のまま、ダイスありなら解析に使われる（テストで確かめた）。上の「判断が要る点」の既定の件はこれで置き換わる。`TODO.md` の TODO-159 の節にこの決定を書き足した
2. テスト: `buttons()` が返すキーを行の名前（`cubeValue`・`cubeHold`・`cubeDouble`）にし、`app.js` の seg の表示は `{ ...BgCube.buttons(s.cube), onRoll: ... }` で受ける形にした（入れ替える余地が無く、その形の文字列と `buttons()` の値をテストで見る）。`test_cube_settings_buttons` に、既定（onRoll が白・黒 × ダイスあり・なし）と、`request` を通したあとの次に振る人・`doubled` を足した
   - 壊すと落ちるか（`test_cube_settings_buttons`）: ① `buttons` の Hold と Double を入れ替える ② `offered: !dice` を `!!dice` にする ③ `other(onRoll)` を `onRoll` にする ④ `app.js` の `...BgCube.buttons(s.cube)` を外す。4 つとも落ち、戻すと通った
3. `analyzer/README.md`（ダイスの設定の説明、キューブの既定の説明）と `docs/raspi.md:129` を、「…側に置く」「…に対してダブル」の言い方に直した
- 確認: `uv run pytest analyzer/test_pwa.py`: 33 passed、`node` で `app.js`・`cube.js` の構文を読み込み通った。画面は見ていない（verifier の担当）
