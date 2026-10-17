# TODO-113 reviewer の報告（`git diff main...HEAD`、7c5c95f）

実測は Playwright（`/usr/bin/chromium`）で、`board.js`・`board-view.js`・`style.css` だけを読んだページに
`BgBoardView.draw(..., onSelect, onPart)` で描き、`elementFromPoint` で当たりを調べた
（スクリプトは scratchpad。アプリ全体は動かしていない）。

## 要修正

1. `tools/ui_snapshot.py:4`（docstring）/ 69 / 112-117 / 230
   - 何が: docstring は「クリックだけで操作し、app.js の中は読みも呼びもしない（nothing inside app.js is read or called）」と書いているが、
     今回 `sheet: BgApp.state.sheet` を読み、`sheet_for` が `BgApp.update({ sheet })` でシートを開け閉めし、flow_photo が
     `BgApp.update({ homePick, bottomColour })` を呼ぶようになった。
   - なぜ: main の ui_snapshot.py は `BgApp` を一度も使っていない（`git show main:tools/ui_snapshot.py | rg BgApp` で 0 件）。
     文書と実装が食い違う。加えて SNAP の冒頭のコメント「A part that is hidden ... is recorded as null」の考え方（見えているものだけ）
     からも外れる。シートが見えているかは `shown` の id の一覧に `sheet-match`・`sheet-cube`・`sheet-roll` を足せば
     見えるものだけで取れる。開け閉めも `part(kind)` と `.sheet-close` のクリックでできる。
     flow_photo の homePick は画面で選べなくなったので、docstring 側に例外として書くかどうかは管理者の判断。
2. `TODO.md:120` — 「決めた案で直す」のチェックが入っていない。
   - なぜ: `~/.claude/CLAUDE.md`「チェックボックスは実装できた時点で入れる（確認の担当に回す前）」。実装はコミット済み。

## 検討

3. `analyzer/static/app.js:356-359`（シートの状態が残る）
   - 何が: `state.sheet` を null に戻すのは ✕（359 行）だけ。`go()` も `startPhoto()` も戻さない。シートを開いたまま戻る・
     別の写真を読む・結果の画面から戻ると、盤面の画面に入った時点でそのシートがまた開いている。
   - さらに `.sheet` は `z-index: 20`、下のバー（`.actbar`）は `z-index: 6`（style.css:72、281）で、どちらも `bottom: 0` に固定。
     シートが開いている間は「解析する」がシートの下に隠れ、✕ を押すまで押せない。
   - 根拠: コードを読んで確認（`rg -n "sheet:" analyzer/static/app.js` は 80・354・359 行だけ）。画面では未確認。実害は未確認。
4. `analyzer/static/board-view.js:235-250`・`94`（ダイスの「?」がポイントのタップを取る）
   - 何が: 盤面の画面では、ダイスがいつも（振る前も点線の「?」で）描かれ、`.tap` で当たりを持つ。ダイスは `.hit` より後に
     描くので上に重なり、次に振る人の側のフィールドの 3・4 列目（上下で計 4 ポイント）の、真ん中寄りの 5 段目の一部
     （SVG の y 204〜236）をタップするとシートが開き、駒を置けない。
   - 根拠: 実測。2 単位おきの格子で「下に `.hit` があるのに一番上が `.tap`」の点が、ダイス無し 590 点・4-2 で 604 点、
     列は white のとき 9・10（左端から 48 単位ごと）、black のとき 2・3、y は 204〜236。main ではダイスが `pointer-events: none`
     で、ダイス無しのときは何も描かないので、この重なりは無かった。5 段目のタップ（5 個以上の所で 1 個ずつ増える）は
     y 176〜203 では今も効く。どの程度困るかは未確認。
5. 色が逆のまま読んだときの直し方（`analyzer/README.md:62`、`app.js:612`）
   - 何が: `bottomColour` は端末に覚えないので（`app.js:56` の初期値 1、localStorage に無い）、アプリを開き直した最初の写真は
     いつも「手前が明るい駒」で読む。recognizer は色を逆にすると左右も逆に推測する（`recognizer/board.py:183`、
     recognizer/README.md:228）ので、暗い駒の人は PIP と置き場の 2 回のタップが要る。四隅の画面で先に選ぶ手段は無くなった。
   - README の 62 行は「違えば盤面の画面で直す」だけで、左右も逆になることは 228 行（recognizer/README）にしか無い。
     また「前の写真のまま」は、開き直した直後は当たらない（明るい駒になる）。ユーザーが決めた案どおりなので、文書に足すかどうかの判断だけ。
6. 置き場のタップは `homePick` を変えない（`app.js:349-350`、944）
   - 何が: 四隅の画面に戻って読み直すと、`homePick` が "auto" なら推測し直し、置き場で直した左右が戻る。
     TODO-126 より前の履歴の写真で `homePick` が "left"/"right" のものは、その値がずっと送られ、画面で "auto" に戻す手段が無い。
   - 根拠: コードを読んで確認。main でも盤面の画面の図（home-svg）は `setHome` だけで同じだったが、main では四隅の画面で選び直せた。実害は未確認。
7. `analyzer/static/style.css:276` — `.die` の `pointer-events: none` とコメント「taps go to the point under the dice」が今は当たらない。
   - 盤面の画面のダイスとキューブは `.tap`（277 行）で上書きされ、結果の画面は `#result-svg { pointer-events: none }`（318 行）で
     全部止まり、写真の盤面図はダイスもキューブも描かない（board-view.js:90 の `if (photo) return`）。`.die` を指定している所が無くなった。
8. `recognizer/README.md:16` — 「アプリでは「自分の色」を選んでもらいます」が古い。今は盤面の画面で PIP をタップして直す。差分に含まれていない文書。
9. `analyzer/static/app.js:285` — コメント「only then: the setting above shows the side (TODO-086)」の「the setting above」（ホームの図）が無くなった。

## 好みの範囲

10. `app.js:349` の `tapPart(kind)` と `board-view.js:61` の `tapPart(e, kind, onPart)` が同じ名前で別の働き。読むときに取り違えやすい。

## 問題なし（1 行ずつ）

- board-view.js `draw` の match の条件: onPart が無い盤面図（結果・写真）は main と同じ（長さ 0 なら行を出さない）。盤面の画面だけアンリミテッドでも出す。
- `drawDice` の dice が null: `rolled()` は両方そろうか null（app.js:92-96）なので、片方だけの [3,0] は来ない。結果の画面は main と同じく描かない。
- タップの当たり: `.tap`（0,2,1）が `.die`（0,1,0）に勝ち、子の `pointer-events="none"` 属性（表示属性）は `.tap *` で上書きされる。トレイの上の上がった駒は `none` のままでトレイに通る。マッチの文字は字間も含めて 99% 当たる（実測）。
- `#match` の移動（app.js:142）: 盤面の画面ではシートの中の `#board-match` に戻り、四隅の画面では `#corners-match` に出る。シートが閉じていても四隅の画面には影響しない。test_pwa.py:356 の文字列もそのまま通る形。
- `homePick` の初期化（app.js:609）: 新しい写真はいつも "auto"、履歴は `kept.homePick || kept.home`、それも無ければ "auto"。main の「新しい写真は前の選択を引き継ぐ」は選ぶ画面が無くなったので不要。
- シートの表示条件の `s.step === "board"`: シートは `#board` の section の中なので無くても隠れるが、害は無い。
- tools/pi_ui_check.py: main は `#home-pick` の隅をクリックして homePick と bottomColour を正解に合わせていた。今は同じ値を update で入れるので、読み取り以降で確かめていることは同じ。
- tools/ui_snapshot.py の flow_manual: main は far-right（色を入れ替え、ホームは右のまま）→ far-left（左へ）。今は colour → home（右→左）で同じ状態を通る。シート 3 つの開け閉めの snap が足された。
- 消し忘れ: `drawHomePick`・`cornerOf`・`onCorner`・`home-pick`・`home-svg`・`.home-pick` の CSS・SEGMENTS と seg の homePick は、archives と TODO.md の外には残っていない（`rg` で確認）。
- 版: analyzer 0.70.1 → 0.71.0（機能の変更なので minor）、`APP_VERSION` も 0.71.0。recognizer は README だけなので上げない（CLAUDE.md「バージョン」どおり）。
- README.md の構成図・analyzer/README.md の手順 2・3・recognizer/README.md:228 は実装と合っている（上の 5・8 を除く）。
- テスト: board-view の描画を DOM で確かめるテストは main にも無く、今回も足していない。確認は ui_snapshot と TODO.md の「ローカル:」の行に頼る形。

## 作り込みすぎ

- `tools/ui_snapshot.py:114`: delete: `try { ... } catch (_) {}`。渡す selector はすべて CSS（`rg -n "r\.(click|choose|seg)\(" tools/ui_snapshot.py`）で、例外は起きない。`const e = q && document.querySelector(q);` の 1 行。（好みの範囲）
- `style.css:276-277` + `board-view.js:212-213, 220, 228-229` の PIP・マッチ・スコアの `"pointer-events": "none"`: shrink。これらの札は盤の外の行にあり、下に `.hit` が無いので `none` で通す先が無い。属性を消せば `.tap *` も要らず、`.die` を 276 行から外せば 277 行は `cursor: pointer` だけになる。（好みの範囲）

net: -3 lines possible.

---

# 2 回目（782b1c0 だけ）

コードを読んで確かめた。ui_snapshot の記録とアプリの画面は流していない。

## 要修正

1. `tools/ui_snapshot.py:194`、`228-233`（flow_photo が screen1 を逆の色で読む）
   - 何が: flow_manual の `r.part("colour")` が、アプリの `keep("bottomColour", "0")` で localStorage に「手前は暗い駒」を残す。
     `record` はすべての flow で同じ `ctx`（279 行）を使い、`INIT` は `collect` しか触らないので、次の flow_photo の新しいページでは
     `state.bottomColour` が 0 で始まる（app.js:56）。新しい写真はこの色で読み（app.js:612）、screen1 の正解は `bottom_colour: 1`、
     `home: left`。前は flow_photo が正解の色とホームを入れていたが、それを消したので、逆の色で読み、ホームも逆に推測しかねない
     （recognizer/README.md:228）。
   - 結果: `record ... manual photo` と `record ... photo` で、photo の記録が変わる。flow を流す順が同じなら毎回同じ記録にはなるので、
     比べること自体はできる。ただし、写真の flow が正解どおりに読めていることを前提にした記録ではなくなる。
   - 根拠: コードを読んで確認（FLOWS の順は manual → photo → history、268 行）。実際に記録を取って読み違うかは未確認。

## 検討

2. `analyzer/README.md:62`「手前の駒の色は端末に覚えた色（盤面の画面で最後に選んだ色。初めは明るい駒）で読む」
   - 履歴から写真を開くと、`state.bottomColour` がその写真の色になる（app.js:612 の `kept.bottomColour`。`keep` は呼ばない）。
     その後の新しい写真は、端末に覚えた色ではなく `state.bottomColour`（開いた履歴の写真の色）で読む。localStorage の値が
     使われるのは、アプリを開いた直後の `state` の初期値だけ。README の書き方と、この場合だけ食い違う。実害は未確認。
3. `analyzer/static/app.js:55` の `homePick` のコメント「or "left"/"right" as kept with a photo picked before TODO-113」
   - 置き場のタップでも "left"/"right" になる（app.js:352-354）ようになったので、コメントが足りない。

## 問題なし（1 行ずつ）

- `stored`・`keep` は 25・28 行の `const` で、`state`（38 行〜）より前にある。`Number(stored("bottomColour", ["0", "1"], "1"))` は 0 か 1。
- PIP のタップ: `keep` に渡す値は入れ替えた後の色（`state.bottomColour ? "0" : "1"` を `update` の前に計算）で合っている。
- 置き場のタップ: `setHome` の後に `homePick` を同じ値にする。読み直すと直した左右で読み、新しい写真は `startPhoto` で "auto" に戻る（609 行）。前の写真の "left"/"right" も、置き場で入れ替えられるようになった。
- `go()` の `sheet: null`: 戻る（`goBack` → `go`）、読み取り後の `go("board")`、解析の `go("outcome")` のどれでも閉じる。
- シートの位置: `--bar-h` は `ResizeObserver` で `#actbar` の高さを追い続ける（app.js:1284-1286）ので、「解析する」の上の理由の行が増えてもシートはバーの上に出る。
- `style.css:276-277`: `.die` を外しても、結果の画面は `#result-svg` の `none` で、写真の盤面図はダイスを描かない。コメントも今と合う。
- `ui_snapshot.py` の `sheet_for`: 開いているシートと要るシートが違うときだけ ✕ → 盤面図の部品をタップする。シートの外のもの（四隅の画面の `#match` も、そのときは `#corners-match` にある）なら閉じるだけ。✕ そのもののクリックは、そのシートが開いていれば何もしない。`BgApp` は SNAP も含めて使っていない（docstring どおり）。
- `recognizer/README.md:16`、`app.js:285` のコメント、analyzer/README.md のシートとダイスの 5 段目の記述は、実装と合っている。
- TODO.md:120 にチェックが入った。

作り込みすぎ: なし
