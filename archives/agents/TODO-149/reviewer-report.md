# TODO-149 レビュー報告（reviewer）

対象: `git diff main...HEAD -- analyzer`。コードは読んだだけで、実行はしていない（見なくてよいと指定されたため。実害は未確認）。

要修正 0 件 / 検討 2 件 / 好みの範囲 1 件。

## 問題が無い点

- 5 つの画面の出る／出ないは仕様どおり（`previousStep` app.js:555 を読んで確認）。
  - 写真の選択: 戻る先が photo なので出ない。
  - 四隅: 同上で出ない。
  - 手で入力した盤面（`fromPhoto` false、app.js:723 の `setUpByHand`）: photo なので出ない。
  - 写真から進んだ盤面（`fromPhoto` true、app.js:641 の `startPhoto`）: corners なので出る。
  - 結果: board なので出る（手入力から来た結果でも出る。仕様の「結果の画面では出る」どおり）。
- キーと描画の中身: `previousStep()` が読む `state` の値は `step` と `fromPhoto` だけで、キー `[s.step, s.fromPhoto]` と一致する。ずれる場面は無い。描画関数は引数の `s` でなく `state` を読むが、`render()` は `state` そのものを渡しているので同じ。
- 登録位置: `previousStep`（app.js:555）の後ろ、`part` の定義（app.js:123）の後ろ。`previousStep` が実際に呼ばれるのは最初の `render()` からで、それは `update()`（ハンドラや `loadSharedPhoto` の中）からしか起きず、ファイルの読み込み中に呼ばれる `update`／`render` は無い（app.js の 560 行より前と 1380 行より後を `rg` で確認）。TDZ の問題は無い。初回の描画前の見た目は `index.html` の `hidden`（261 行）で、写真の選択の画面では隠れたまま。`p.last` の初期値 `{}` と文字列のキーは一致しないので、最初の `render()` で必ず 1 回描く。
- `startPhoto` が写真の選択の画面のまま `fromPhoto: true` にする場面は、`step` が photo なので戻る先は photo のまま。出さない状態を保つ。
- バージョン: `app.py` の `__version__` と `app.js` の `APP_VERSION` が 0.81.1 で揃っている。直しなので 0.81.0 → 0.81.1 は CLAUDE.md の規則どおり。recognizer は触っていないので上げない。
- `analyzer/README.md:95` は新しい条件に直してある。ほかの文書（`docs/`、`CLAUDE.md`、`recognizer/README.md`）に「最初へ」の記述は無い（`rg` で確認、archives と TODO.md を除く）。

## 検討

1. `analyzer/static/index.html:260` / コメントが古い
   - 「写真の選択の画面のほかはどの画面にも出す（TODO-148）」のまま。実装は四隅と手入力の盤面で出さなくなった。
   - 根拠: 差分に `index.html` が含まれていない。`rg "最初へ|to-start"` で確認。

2. `analyzer/test_pwa.py:527-534` のテスト
   - 関数名 `test_every_screen_but_the_first_can_go_back_to_it` と 528 行のコメントが「写真の選択以外のどの画面でも」のままで、新しい挙動と食い違う。
   - テストは `hidden = previousStep() === "photo"` の文字列だけを見ていて、キー `[s.step, s.fromPhoto]` は見ていない。キーから `s.fromPhoto` を外しても落ちない。外すと、手入力の盤面と写真から進んだ盤面で `step` が同じ "board" のままなので、直前の描画が残って「最初へ」の出る／出ないが入れ替わらない（未確認。推測ではなく `render()` の `ks === p.last` の読みから）。部分文字列の確認なので、壊すと落ちるのは条件式の変更だけ。

## 好みの範囲

- app.js:557-558: 新しい `part` を足さず、既存の `part((s) => s.step, ...)`（app.js:140）のキーを `[s.step, s.fromPhoto]` にして、`to-start` の行をそこに残せば 2 行減る（作り込みすぎの節: `L557-558: shrink`。`previousStep` は描画時に呼ぶだけなので定義の順序に問題は無い）。ただし、`s.step` のキーで走る処理にタイトルや進行表示の描画が混ざる。今の分け方でも読める。

作り込みすぎ: なし（上の shrink 1 件のみ）。

net: -2 lines possible.
