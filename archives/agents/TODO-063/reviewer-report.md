# TODO-063 reviewer の報告

対象: `git diff main..claude/board-colours`（46c7d8e）。コードは直していない。

## 要修正

1. **docs/PI_CHECKS.md:92-100（PI-046）/ 必ず書く欄が欠けている。**
   同じファイルの 72 行目に「『確かめ済み』『ここで確かめること』『無駄を省く工夫』は必ず書く」とあるが、
   PI-046 には「確かめ済み」「ここで確かめること」が無い（直前の PI-045 も同じく欠けているので、前例を写した形）。
   内容は「無駄を省く工夫」の行にすでに半分書いてある（色と並びは TODO-063 で画面を撮って確かめた → 確かめ済み、
   スマホでの見え方と版 → ここで確かめること）ので、行を分けるだけで足りる。

## 検討

2. **docs/PI_CHECKS.md:94 / 担当とチェックボックスが合わない。** 担当は「ユーザー（スマホ）」だけだが、
   `- [ ] Pi: 更新して /version が analyzer 0.42.0 か` があり、本文にも「Pi の Claude Code は版を見るだけでよい」とある。
   担当に Pi の Claude Code を足すか、Pi の行を外すか（版はクラウドからも `tools/check_pi.py` で見られる）。
3. **analyzer/static/board.js:64 / コメントが古い。** `A tap at level (1..5 from the board's edge) of a point or of the bar's half`
   のままで、バーは真ん中から数えるようになった。board.js の処理は level の数え方に依らないので実害は無いが、
   board-view.js:120 と tools/ui_snapshot.py:112 は「バーは真ん中から」に直してあり、ここだけ残っている。

## 好みの範囲

4. **analyzer/static/icon.svg:7-10** は前の配色（#f3efe4・#3a2a4a、縁 #555）のまま。アイコンは依頼の範囲外なので、揃えるかはユーザーの判断。

## 問題の無かった観点

- バーの上下の入れ替え: drawBar の描画（white→top、black→bottom）、bindTap の side（`top ? "white" : "black"`）、
  drawMove の `stackY(mover === "white", level, true)`、stackY の bar 分岐はすべて「手前＝上」で揃っている。
  stackY の呼び出しは drawStack と drawMove の 2 か所だけで、どちらも直してある。漏れ無し。
- タップの高さと駒の位置（MID=220、半分=196）: k 個目の中心は真ん中から 29+36k。
  `floor((d-9)/36)+1` に中心を入れると k+1 になる。帯の境目（9+36k）は、上に重なる次の駒の縁（29+36k-20）とちょうど一致する。
  真ん中から 9 未満（ラベルのあたり）は 1 に丸まる。5 個目の外側の縁は上 27・下 413 で、盤の縁（24・416）の内側に収まる。
  「バー」の文字（ベースライン 225、13px）は上の駒の縁 211・下の駒の縁 229 の間にあり、駒と重ならない。
- tools/ui_snapshot.py の tap(): 真ん中からの距離は 27+36(level-1) で、上の式に入れると level に戻る。
  k=24（上半分）は rect の下端から、k=25 は上端から測っていて合っている。
  なお 162 行目の `r.tap(25, 1); r.tap(24, 2)` は手前と奥が入れ替わるので、0.41 と 0.42 の記録を compare すると
  "bar" の場面に差が出る。今回の変更どおりの差。77 行目の colours も 16 進から `var(--light-chk)` のような値に変わる（入れ替わりは見分けられる）。
- CSS 変数の入れ子: Chromium（/usr/bin/chromium、Playwright）で実測。:root のインライン style に
  `--white-chk: var(--dark-chk)` を入れると、`.chip` 相当の background と SVG の `style.fill: var(--white-chk)` が
  入れ替わった色（rgb(28,28,28) など）になった。.chip・.winbar は --white-chk・--black-chk・--*-fg を使うだけで、どれも入れ替え後も定義されている。
  ダークモードの @media は駒の変数を上書きしないので影響しない。board-view.js の el() は `var(` で始まる値を style に入れるので、新しい stroke の var() も効く。
- 版: analyzer/app.py と app.js の APP_VERSION が 0.42.0 で一致（機能の変更なので 0.41.0→0.42.0 は CLAUDE.md どおり）。
  sw.js の CACHE も上がっている。recognizer は変わっていない。
- analyzer/README.md:44 の記述は実装と合う。ほかの文書（README.md・docs/・recognizer/README.md・CLAUDE.md）に、
  バーの上下や盤の配色を書いた箇所は無い（`rg -e 'バー.*(上|下)半' -e '配色' -e 'felt'` で確認）。
- 範囲: 差分は依頼の範囲内。コメントは「なぜ」（ラベルを避ける、入れ替えは app.js）を書いている。
- テスト: 描画だけの変更で、analyzer の pytest の対象外。確認は verifier の担当。

## 作り込みすぎ

作り込みすぎ: なし（app.js の入れ替えは 3 変数を 1 つのループにまとめて短くなっている。
style.css の `--white-*`/`--black-*` の既定値 6 行は app.js が起動時に必ず上書きするが、JS の前の表示用の既定として残す意味はある）。
