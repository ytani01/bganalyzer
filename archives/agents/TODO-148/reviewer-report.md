# TODO-148 reviewer の報告

対象: `git diff main...HEAD`（6c353ac）。コードを読んだだけで、実行はしていない。

## 要修正

なし。

## 検討

### 1. `analyzer/test_pwa.py:526-534` / `goStart` の中身を壊してもテストが落ちない
- **何が問題か:** テストが見ているのはボタンの並び順と、`hidden` の行・`addEventListener` の行の文字列だけ。
  `goStart` の `go("photo")` を `go("board")` に変える、`if (inApp) history.back();` を消す（履歴を使い切らない。
  この項目の要の仕様）、といった壊し方をしても通る。
- **根拠:** 読んだコード（test_pwa.py の追加分と app.js:566-570）。同じファイルの app.js 向けテストも文字列の
  有無で見ている（例: 直前の `test_board_can_be_fixed_on_the_result_screen`）ので、そのやり方に沿うなら
  `goStart` の本体（`go("photo");` と `history.back();`）の文字列も確かめれば、少なくとも上の 2 つの壊し方で落ちる。
  `goBack` にもテストは無い（既存）。

### 2. コミットが 1 回だけ（項目を立てるコミットが無い）
- **何が問題か:** `main..HEAD` は 6c353ac の 1 つで、TODO.md への項目の追加と実装が同じコミットに入っている。
- **根拠:** ~/.claude/CLAUDE.md「コミットは 2 回に分ける。立てるとき `docs(todo): …を TODO-NNN として立てる`、
  済んだら `feat(...)`」。コードではなく手順の話なので、扱いは管理者の判断。

## 好みの範囲

### 3. `tools/ui_snapshot.py:66` / 記録する要素の一覧に `to-start` が無い
- 差分の外。一覧に無いので、`ui_snapshot.py compare` では「« 最初へ」の出る・出ないの変化を拾えない。
  足すと既存の記録との比較で差が出るので、足すかどうかは判断が要る。

## 指摘の無い点

- 履歴: 写真の選択以外の画面では `go()` が必ず `{bg:true}` を積むので `inApp` は実際には常に真。`go("photo")` で
  画面を先に変え、`history.back()` の popstate は `state.step === "photo"` で何もしない。履歴は 1 つだけ減り、
  余計な遷移は起きない（app.js:543-570・1233-1236 を読んで確認。実機は未確認）。
- 解析中（`state.busy`）: `#busy` は `position: fixed; inset: 0; z-index: 20` で、下のバー（z-index 6）を覆う
  （scanning のときも透明だが覆っていて、タップは skip に行く）ので押せない（style.css:72・267 を読んで確認）。
  押せたとしたら popstate が `{bg:true}` を積み直し、写真の選択の画面で履歴が 1 つ残るが、押せないので実害は未確認。
- `history.back()` の popstate が届く前に写真の選択の画面で解析を始めると、popstate が `{bg:true}` を積み直す
  余地はある。ミリ秒の間の話で、実害は未確認。
- 後始末: `goStart` も `go("photo")` を通るので、`stopSpeaking()`・`reanalyzeAbort.abort()`・`sheet: null`・
  `historyShown++` は `goBack` で写真の選択に戻るときと同じ。`reanalyzeTimer` は step で動く part が消す。
  結果から盤面を経ずに写真の選択へ行くことで抜けるものは見当たらない。
- バージョン: analyzer のコードを変える機能の追加で 0.80.0 → 0.81.0、`APP_VERSION` も同じ。recognizer は触っていない。規約どおり。
- コメント: `goStart` のコメントは popstate が何もしない理由を書いていて「なぜ」になっている。
- 範囲: README の「ヘッダーの戻る」を「画面の下の「‹ 戻る」」に直したのは指示の外だが、TODO-107 で戻るが下に移った
  ことに合わせた古い記述の訂正で、同じ文の中。
- 文書: 「最初へ」「戻る」で README・docs・tools を `rg` し、古い記述は見当たらない。TODO.md の残りの項目と次の番号も更新済み。
- TODO.md: `- [ ] ローカル:` の行があり、CLAUDE.md の「マージ後に確かめること」どおり。

## 作り込みすぎ

- `analyzer/static/app.js:567-569`: shrink: `inApp` の一時変数。`go("photo")` は写真の選択では履歴を積まず
  `history.state` を変えないので、`go("photo"); if (history.state && history.state.bg) history.back();` で同じ。
  好みの範囲。

net: -1 lines possible.
