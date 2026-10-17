# TODO-116 reviewer の報告

対象: `git diff main...claude/todo-116-analyze-disabled`（69792aa）。コードを読んで確かめた（画面の操作はしていない）。

## 要修正

### 1. 手前の色を変えると、理由の文の「白／黒」が古いまま残る

- 場所: `analyzer/static/app.js:161`（新しい part の key）、`app.js:160`（`BgBoard.errors(s.board, NAME)`）
- 内容: `NAME` は `BgResult.NAME` で、`app.js:185` の part（key は `s.bottomColour`）が `BgResult.setNames` でその中身を書き換える（`result.js:10-11`）。
  新しい part の key に `s.bottomColour` が無いので、色だけ変えると描き直されない。
  - 「手前の駒の色」（`SEGMENTS.bottomColour`、`app.js:1180`）だけを押した場合: 盤は同じで key が変わらず、「白の駒が 16 個あります」のまま、手前の人が「黒」と呼ばれる画面になる
  - 「色を入れ替え」（`app.js:1148-1151`）の場合: 1 回目の `update`（盤の入れ替え）で描き直されるが、そのときの `NAME` はまだ前の色の名前。2 回目の `update`（`bottomColour`）では key が変わらず、名前の違う文が残る（白 16 個の盤で押すと、正しくは「白の駒が 16 個」のところ「黒の駒が 16 個」と出る、と読んだ）
- なぜ問題か: 前は押したときに文を作っていたので、いつも今の名前だった。この差分で入った食い違い。
  同じ `NAME` を使う駒の数の印の part（`app.js:256`）は、key に `s.bottomColour` を入れ、`setNames` の part（185 行）より後ろで登録してある。
  新しい part は 161 行で `setNames` の part より前にあるので、key に `s.bottomColour` を足すだけでは同じ render の中で古い名前を使う（parts は登録の順に描く。`app.js:116-124`）
- 実害: コードを読んでの判断で、画面では確かめていない

## 検討

### 2. index.html の TODO-115 のコメントが、そのラベルから離れた

- 場所: `analyzer/static/index.html:258-261`
- 内容: 「盤面の画面だけ。オンなら、解析して結果の画面に移ったら読み上げる（TODO-115…）」は `#auto-speak-opt` の説明だが、間に TODO-116 のコメントと `#analyze-why` が入り、`#analyze-why` の説明に見える
- なぜ問題か: 周りはどれも「コメントのすぐ下がその要素」の形（`#hdr-reuse`・`.actrow`）

### 3. テストは文字列があるかだけで、key の抜けは捕まえられない

- 場所: `analyzer/test_pwa.py:350-352`
- 内容: 周りのテストと同じ書き方で揃ってはいる。ただ 1. のような「key に足りないものがある」は落ちない。`app.js` を `node` で動かすテストはこのファイルに無いので、ここで足すのは重い。直すかどうかは管理者の判断
- 好みに近い。挙げるだけ

## 問題が無かった点

- key `[s.step, s.board, s.match.crawford, s.cube.at]`: 盤面の編集（`fixBoard`・`editBoard`）、元に戻す（`app.js:1122-1125`）、写真の読み取り、`setMatch`・`setCube` はどれも `update` を通り、`render` は key を `JSON.stringify` で比べるので、盤を書き換えても追いつく（色の名前だけが 1. の例外）
- TDZ: `crawfordCube`・`CRAWFORD_CUBE`・`analyzeErrors` は 155-160 行で、使うのは part の中（render 時）と `recognize`（876 行）・`analyze`（887 行）の関数の中だけ。155 行より前の上の段に呼び出しは無い。`recognize` の `analysis_error` の alert は前と同じに動く
- 盤面の画面以外: key に `s.step` があり、`errs` は `[]` になるので `disabled` は外れ、`#analyze-why` は隠れる。`#analyze` を `disabled` にする所はほかに無い
- 下のバーの高さ: 理由が出てバーが高くなっても、`--bar-h` の ResizeObserver（`app.js:1216-1218`）が `main` の下の余白を合わせる
- `analyze()` の 1 行の早期 return は、ボタン以外の呼び出し口は無いが、サーバーに送る前の安い守りなので残してよい
- 版: analyzer 0.65.1 → 0.66.0 は機能の変更なので CLAUDE.md の「バージョン」に合う。`APP_VERSION` も同じ
- README: 70 行・79 行の書き換えは挙動と合う。63-64 行（駒の数の印と「解析できない」）も今の挙動と食い違わない。ほかの文書（`docs/`・ルートの README）に古い「止める／alert」の記述は無い（`rg` で確かめた）
- style.css: `var(--warn-fg)` は `.alert` と同じ色の変数。`[hidden]` を打ち消す `display` は無い
- 範囲: 指示に無い変更は無い

## 作り込みすぎ

作り込みすぎ: なし（`analyzeErrors` は part と `analyze()` の 2 か所で使う）。Lean already. Ship.
