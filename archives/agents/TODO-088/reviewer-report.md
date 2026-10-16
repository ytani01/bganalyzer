# TODO-088 reviewer の報告

対象: 未コミットの `git diff`（ブランチ claude/todo-088-fix）と `implementer-report.md`。実測はしていない（別の担当）。

## 要修正

### 1. `tools/ui_snapshot.py:209` が、もう無い写真のタップの領域を押しにいく

- 場所: `flow_photo` の `r.seg("photoView", "side"); r.point(3, "#photo-svg"); r.snap("tap on the photo")` と、続く `r.click("#undo"); r.snap("undo the tap")`
- 問題: `point()`（:115）は `#photo-svg .hit` の 4 つ目を押す。`app.js:303` で `#photo-svg` に `select` を渡さなくなり、`board-view.js:94`・`:112` の `if (!onSelect)` で `.hit` が作られないので、locator が見つからない
- 起きる場面: `ui_snapshot.py record` で `flow_photo` を流すと、Playwright の既定の待ち時間（30 秒）のあと TimeoutError で止まる（コードを読んだだけ。実行はしていない）。続く「undo the tap」も前提が無くなる。写真をタップして盤面が変わらないことを記録する手順（例: `#photo-svg` の中央を `page.mouse.click` して snap）に置き換えるか、2 行とも消すかは管理者の判断
- 根拠: 依頼の「消した id・文に頼る所（`tools/`）」。implementer の報告の `tools/ui_snapshot.py` の項にこの行が無い

## 検討

### 2. `style.css:125` `#corner-help` の `min-height` を 1.5em にしたので、文の行数が変わると写真が上下に動く

- 場所: `analyzer/static/style.css:125`（スマホ用の `min-height: 3em` も削除）、文は `app.js:221-229`
- 問題: 1 行の `fit` 以外に、2〜3 行になりうる文が残っている（「四隅をやり直す」のあとの「枠の内側の四隅を、手前から見て 1. 左上 の順にタップしてください。」、見つからないときの「盤を見つけられませんでした。＋fit＋切り抜いて…」）。前は 4.5em／3em でこれらの高さを取ってあり、`app.js:218` のコメント（文の高さが変わると指の下の写真が動く）もそれを前提にしている
- 起きる場面: 「四隅をやり直す」で 4 つ目をタップした直後に文が 1 行に縮み、写真と点が上へずれる。「探しています…」から「見つけられませんでした…」に変わるときは下へずれる。ドラッグ中は `s.dragging` で書き換えないので、指の下で動くことは無いはず。390px 幅で何行になるかは未確認（実害未確認）

## 好みの範囲

### 3. `#errors` の id と中身がずれた

- 場所: `index.html:131`、`app.js:257-259`
- 問題: 数の誤りを出さなくなり、中身はサーバーの `warnings` だけ。id は `errors` のまま
- 起きる場面: 読む人が「解析を止める誤り」の表示だと思い込む。`ui_snapshot.py` の `errors` も同じ。直さなくても動きは変わらない

## 観点ごと（問題の無かったもの）

- 写真が押せないこと: `app.js:303` で `select` を渡さず、`board-view.js:94`・`:112` で `.hit`／`.hit-num` を作らない。問題なし
- 盤のタップ・長押し・スクロール: `git diff 854d7e8^ -- analyzer/static/board-view.js` が空。TODO-086 の style.css の変更にも `touch-action` などの触れ方の変更は無い。問題なし
- ルーペの残り: `board-view.js`・`style.css`・README から盤のルーペは消えている。残る「ルーペ」（`README.md:85`、`analyzer/README.md:44`、`ui_snapshot.py:224`）はどれも四隅の画面のルーペ（`corners-view.js`）。問題なし
- 解析の設定の並び: HTML の並びが変わっただけで、`app.js:309-316`（`dice-row` は `cubeOffered` で隠す）と `:334-345` は変えていない。ダブルされたところでダイスを使わない規則（`BgCube.request`、`rolled`）も変わっていない。問題なし
- 数のずれの印: 前の `#errors` は「15 個より多い／駒が無い」があると上がりの文を出さなかったが、新しい印は両方を並べる（例: 「⚠ 白 17/15・黒 14/15」）。どちらが多い／少ないかの中身は前と食い違わない。解析を止める条件は `app.js:870` の `BgBoard.errors` の `alert` で残っている。いつも出ていた上がりの数は、盤面図のトレイ（`board-view.js:170`）に残る。問題なし
- 「写真」の印: `app.js:313`・`:338` の条件は変えておらず、id もそのまま。印を `dice-row` の中へ移したので、ダブルされたところでは行ごと隠れる（前も隠していた）。問題なし
- 消した id・文への参照: `counts`・`flip-turn`・消した文言を `rg`（archives と TODO.md を除く）で探して、残っていたのは上の 1 だけ。`analyzer/test_pwa.py:402-405` は `board.js` の `counts`／`errors` の関数を試していて、画面の要素ではない。docs/ に当たりなし
- 版: analyzer 0.53.0（機能の変更）、`APP_VERSION` 一致、`sw.js` のキャッシュ名も上げてある。recognizer は触っていない。問題なし
- 文書: `analyzer/README.md` の並び・印・写真は見るだけ・「手番を入れ替える」の削除は実装と合っている
- テスト: 印の出し分けは `app.js` の `part` の中にあり、単体テストは無い（前の `#counts`／`#errors` の表示にも無かった）。verifier の実測で見る範囲
- コメント: 「なぜ」が書いてある。範囲外の変更は無い

## 作り込みすぎ

- `app.js:256`: shrink: 隠しているときにも `""` を入れる三項演算。`$("count-mark").textContent = \`⚠ ${mark.join("・")}\`` だけで足りる（`hidden` で見えない）。1 行の中の話で、好みの範囲

net: -0 lines possible（式の短縮だけ）。
