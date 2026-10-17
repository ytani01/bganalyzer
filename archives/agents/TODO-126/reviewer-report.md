# TODO-126 reviewer の報告

対象: `git diff main...HEAD`（ブランチ claude/todo-126-home-corners、78ea20e）

## 要修正

### 1. tools/ui_snapshot.py:175 が消えた seg を押す

`r.seg("home", "left")` が `.seg[data-name="home"] [data-value="left"]` をクリックするが、
この seg は index.html から消えた。Playwright の click がタイムアウトで落ち、`manual` の流れの
記録がここで止まる（コードを読んで確認。実行はしていない）。

直すときの注意: 直前の 174 行で「色を入れ替え」を押しているので、この時点は bottomColour = 0。
鏡写しだけを試すなら `#home-svg [data-corner="far-left"]` を押す。`near-left` を押すと
色の入れ替えも起きて 174 行の効果が打ち消される。

### 2. analyzer/README.md の画面の説明が古いまま

- 39〜40 行:「手前の駒の色で『明るい方』を選ぶと…」「四隅の画面の『手前のホーム』『手前の駒の色』など」
- 62 行:「手前の人のホーム側（自動/左/右…）と駒の色（暗い方/明るい方）を選んで」
- 73 行:「画面では『白のホーム』か『黒のホーム』。選び直すと盤を鏡写しにする」

どれも消えた UI を説明している。新しい UI（明るい駒のホームの隅をタップする、奥の隅は持ち主の入れ替え）に
書き換えが要る（CLAUDE.md の冒頭で各部の詳細の参照先にしている文書）。

## 検討

### 3. 四隅の画面の「自動」で、手前の駒の色が見えないまま前の値が残る（判断が要る）

`analyzer/static/app.js:234-235` は homePick が auto のとき隅を何も描かない。一方 `state.bottomColour` は
そのまま残り、読み取りの依頼（app.js:939 の `bottom_colour`）に使われる。次の写真にも
`startPhoto` で引き継がれる（app.js:641）。

- 奥の隅を押したあと「自動」を押すと、bottomColour = 0（暗い方が手前）が画面に出ないまま送られる
- 前は「自動」と「手前の駒の色」が別の行で、自動のままでも色は見えて選べた。今は「自動＋暗い方が手前」を選ぶ手段も無い
- recognizer/README.md:228 にあるとおり、色を逆に選ぶと自動の推測は左右も逆になる。見えない値が読み取りの左右まで変える

仕様（TODO.md の「どの隅も選んでいない状態が自動」）には沿っているが、自動での色の扱いは仕様に書かれていない。
「自動を押したら bottomColour を 1 に戻す」「自動のときも色を何かで示す」「今のまま」のどれにするか、利用者の判断が要る。
実害は未確認（実機で操作していない）。

### 4. recognizer/README.md:228-229 が消えた「手前のホーム」を指している

「アプリで『色を入れ替え』を押したら『手前のホーム』の左右も選び直す」。盤面の画面の項目名は「ホーム」になり、
四隅の画面の「手前のホーム」も無くなった。16 行の「アプリでは『自分の色』を選んでもらいます」も（この差分の前から）古い。

### 5. tools/ui_snapshot.py の SNAP が隅の選び方を記録しなくなった

前は `segs` に `home`・`bottomColour` の選択が入っていた。今は `#home-pick`・`#home-svg` が記録に入らないので、
2 つの版を比べても隅の表示（どの点が選ばれているか、U の向き）の違いは出ない（盤面の向きは `boardSvg`、色は
`colours` で間接に出る）。`html('home-pick')`・`html('home-svg')` を足すかどうか。

### 6. 盤面の画面に同じ働きのものが 2 つ

`#home-svg` の奥の隅（同じ列）を押すと `#swap-colours`（index.html:219）と同じ処理になる。両方残すかは
利用者の判断（ユーザーの追記は「同じ処理にする」で、ボタンを消すとは書いていない）。

## 問題の無かった観点

- 隅 → (home, bottomColour): 行が near なら 1、列がそのまま home。cornerOf と onCorner で往復が一致する
- U の向き: 4 隅すべてで、始点（ホームの列の反対の行）・円弧の sweep・矢じりの向きが board-view.js の drawWay（white = 手前、上から下）と一致した（node で 4 隅の path と drawWay の sweep の式を並べて確認）
- 盤面の画面の 4 隅: BgBoard.swapColours と mirror は順を入れ替えても同じ結果（node で確認）。swapColours も setHome も editBoard を通るので board と read の両方が変わる。押したあとの cornerOf(bottomColour, home) は押した隅になる。同じ隅を押すと何も変わらない
- seg から home・bottomColour を外した影響: 指定の rg で当たる範囲では、上の 1（ui_snapshot.py:175）以外に古い名前を使う所は無い。test_*.py にも当たりは無い
- tools/pi_ui_check.py:60-61 と tools/ui_snapshot.py:209: truth の bottom_colour と home から隅を正しく選んでいる
- 版: analyzer 0.69.2 → 0.70.0（機能の変更）、APP_VERSION も同じ。recognizer は変えていない
- テスト: 隅の対応は app.js の 1 行の式で、自動テストは無いが、pi_ui_check.py が truth の隅を押して読み取り後の home を確かめている（122 行）。足すほどではない
- コメント: 「なぜ」が書かれている。範囲外の変更なし。TODO.md のチェックの付け方も規約どおり

## 作り込みすぎ

作り込みすぎ: なし

---

# 2 回目（`git diff 78ea20e..HEAD`、d9a9bb0・df632d9）

## 要修正

なし

## 検討

### 7. analyzer/README.md:39 に、消えた選択肢の言い方が残っている

「手前の駒の色で『明るい方』を選ぶと手前が白、『暗い方』なら手前が黒」。「明るい方／暗い方」のボタンは無くなった。
「明るい駒のホームが手前の隅なら手前が白、奥の隅なら手前が黒」のように、隅の言い方に合わせるかどうか。
同じ README の 75 行「切り替えの下にそう出す」の「切り替え」も、今は「ホーム」の図のこと（こちらは読めば分かる範囲）。

## 問題の無かった観点

- 1 回目の指摘 1（ui_snapshot.py:175）: 直っている。manual の流れは初期状態（bottomColour 1、home right。setUpByHand は両方を変えない）から始まるので、174 行の far-right で色の入れ替えだけ、175 行の far-left で鏡写しだけが起き、前の 2 つの記録と同じ操作になる
- 1 回目の指摘 2（analyzer/README.md 39〜40・62・73 行）: 直っている（上の 7 を除く）。recognizer/README.md:229 も直っている（1 回目の指摘 4）
- 自動のときの描き分け: auto では U を描かず、bottomColour の行の 2 点を r=5・fill-opacity 0.4 で塗る。auto でないときの描き方は 1 回目と同じ。列に渡す仮の "left" は auto では使われない。盤面の画面（home-svg）は auto を渡さないので変わらない
- 盤面の画面の色の入れ替え: swapColours を onCorner の中に移しても処理は同じ（行が違うときだけ `bottomColour` は 1 − 前の値になる）。swapColours という関数への参照も残っていない
- ボタンを消した後の参照: 指定の rg で当たるのは TODO.md の 170・171 行（経緯の記録）だけ。CSS・tools・テストにも残っていない
- 1 回目の指摘 3（自動で色が見えない）と 6（同じ働きが 2 つ）は、利用者が決めたとおりに入っている
- 版: 0.70.0 のまま（同じ PR の中なので上げ直さなくてよい）

## 作り込みすぎ

作り込みすぎ: なし
