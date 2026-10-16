# TODO-093 reviewer の報告

対象: ブランチ claude/todo-093 の未コミットの差分（`git diff`）。`uv run pytest analyzer/test_pwa.py` は 23 passed。

## 要修正

### 1. analyzer/static/app.js:223 / 四隅の画面の案内文が、なくなった「その他」を指したまま

```js
const again = "盤が小さいときは「その他」の「画像を編集」で切り抜いてください。";   // only when the board was not found (TODO-088)
```

- 何が問題か: 盤が見つからなかったとき（`cornerGuess` が `default` / `missed`）に `#corner-help` へ出す文。
  この差分で四隅の画面の「その他」（`<details>`）は無くなり、「画像を編集」は最初から見えている。
  利用者は無い「その他」を探すことになる。
- 根拠: 読んだコード（app.js:219-229 の part と、差分後の index.html の `#corners`）。
  `rg -n "盤が小さいとき"` でこの 1 か所だけ。テストは文言を見ていない。

## 検討

### 2. analyzer/test_pwa.py:292-295 / 壊しても落ちない壊し方がある

- 何が問題か: 足したテストは、HTML に `<div id="corners-match"></div>` があることと、app.js に移す行が**文字列として**あることだけを見る。
  - `index.html` の `<div id="board-match">` を消す（または `#match` の外へ出す）と、`$("board-match")` が null になり、
    起動時の `go("photo")` で step の part が `TypeError` を出して画面の描画が止まる。この壊し方でテストは通る
    （`id="board-match"` も、それが `#match` を包むことも assert していない）。実害は未確認（実機では試していない。読んだコードからの推定）。
  - 移す行の assert は実装の行をそのまま写した文字列で、書き方を変えただけで落ち、意味が変わっても同じ文字列なら通る。
- 案（直し方は管理者の判断）: 盤面の画面の切り出し（`board`）に `<div id="board-match">` が `id="match"` の直前にあることを assert する。
  行の文字列一致の代わりに `'"corners-match"' in js and '"board-match"' in js` 程度に緩めるかは好みの範囲。

### 3. analyzer/README.md:38 / 「使うことが少ないものは「その他」に畳んである」

- 何が問題か: 四隅の画面には畳んだものが無くなった。盤面の画面の「その他の設定」はまだ畳んである（index.html:212-213）ので誤りではないが、
  どの画面のことかが読み取れない。42 行目（四隅の画面の説明）は直してある。
- 根拠: 読んだ文書とコード。

## 問題なし（1 行ずつ）

- イベントと値: `#match` を `appendChild` で移すだけなので、`change` のリスナーと `<select>` の選択肢・値は要素についたまま。`part((s) => s.match, …)` は id で引くので置き場所によらない。端末に残す値（`setMatch` の `keep("match", …)`）も経路が同じ。
- 最初の表示と画面の切り替え: step の part は key が `s.step` だけで、`last` の初期値が `{}` なので起動時の `go("photo")` で必ず 1 回走る（`#board-match` に置く。もともとそこ）。写真なしで盤面へ・履歴から開く・結果から戻る・戻るボタンは、どれも `go()` → `update({ step })` を通るので、`corners` 以外では `#board-match` に戻る。app.js は body の末尾で読むので、起動時に両方の入れ物はある。
- `#claude-corners` / `#claude-note`: hidden の切り替え（app.js:1177）は id で引くので変わらない。
- `#edit-tools` を出すとき `#corner-tools` を隠す働き: `#corners-match` は `#corner-tools` の中にあるので、編集中は「ゲーム」も一緒に隠れる（ほかの設定と同じ扱い）。
- CSS: `details.more` は四隅の画面では使わなくなっただけで、盤面の画面の `details.panel.more` が使い続けている。`.row` も `margin: 12px 0` なので上下の間は前の `details.more` と同じ。`.opt` `.match` の規則は画面によらない（`#board` に絞った規則は `.boards` だけ）。静的に見た範囲で崩れは無い。
- tools/pi_ui_check.py・tools/ui_snapshot.py: `reveal` は閉じた `<details>` の祖先があるときだけ summary を押すので、無ければ何もしない。呼んでいるのは盤面の画面の「その他の設定」の中のもの（`#export-sample`、`collect` の seg）だけで、壊れない。
- 版: app.py と app.js の `APP_VERSION` が 0.57.0 で揃っている。0.56.0 を飛ばすのは依頼のとおり（TODO-090 と同じ行を触るので、マージの順でぶつかる）。
- 範囲: 指示に無い変更は無い。TODO.md のチェックは実装済みの 2 行だけ。
- コメント: index.html の 2 つのコメントは「なぜ移すか」を書いている。

## 作り込みすぎ

作り込みすぎ: なし（同じ入力を 2 組作らず 1 行で移すのが一番短い）。Lean already. Ship.
