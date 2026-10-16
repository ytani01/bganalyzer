# TODO-086 reviewer の報告

対象: `git diff`（未コミット）と `implementer-report.md`。仕様は `docs/TODO-086-mobile-ui.md`。
コードは直していない。

## 要修正

### 1. Playwright の道具が、閉じた「その他」の中のボタンを押せずに止まる

- 場所: `tools/pi_ui_check.py:96`（`page.click("#export-sample")`）、`tools/pi_ui_check.py:130`（`collect` の seg）、
  `tools/ui_snapshot.py:165`（`#swap-colours`）・`:176`（`#reset-start`）・`:188`（`plies` の seg）
- 何が問題か: これらの要素は閉じた `<details>`（`index.html` の「その他の設定」）へ移ったが、道具は開かずに押している
- 根拠（実測）: 最小の HTML `<details><summary>s</summary><button id="x"></button></details>` を `/usr/bin/chromium` の
  Playwright で開くと、`is_visible("#x")` は False、`getBoundingClientRect()` は 22×21 と 0 でない値、`click("#x")` は
  `TimeoutError`。implementer の報告にある「閉じた details の中のボタンも大きさは 0 ではないと出る」と同じ現象で、
  大きさが出ても押せない
- 起きる場面: CLAUDE.md の「コマンド」にある `tools/pi_ui_check.py`（`export`・`collect`）と `tools/ui_snapshot.py record` が
  タイムアウトで落ちる。TODO.md の「ローカル: 4 画面を一通り操作」で使う見込みの道具。道具そのものを流しての確認は未実施
- 補足: `tools/ui_snapshot.py:57` の `vis('export-sample')` は `closest('[hidden]')` しか見ないので、閉じた details の中でも
  「見えている」と記録する（比べる道具としては食い違いが出ないが、見えていないものを見えている扱いにする）

### 2. クロフォードの警告が、もう無い「ヘッダーのクロフォード」を指している

- 場所: `analyzer/static/app.js:862`（`CRAWFORD_CUBE`）
- 何が問題か: 「…ヘッダーのクロフォードを外してください。」のまま。`#crawford` は盤面の画面の「解析の設定」の「ゲーム」の行へ移った
- 起きる場面: クロフォードのゲームでキューブを片側に置いて「解析する」を押したとき、写真の読み取りで同じ状態になったとき（`alert`）

### 3. `docs/raspi.md` のローカルの確かめ方が、新しい画面と合っていない

- 場所: `docs/raspi.md:128`（`double`: キューブの説明が「ダイスがあるので、最善手を出します。」になる）、
  `docs/raspi.md:132`（`collect`: 「解析の設定」の下のスイッチ）、`docs/raspi.md:182`（PWA の「解析の設定」で「Pi に残す」）
- 何が問題か: `#cube-help` はダイスがあるとき空で隠れるようになり（`app.js:335`、`tools/pi_ui_check.py:74` もそれに合わせた）、
  「Pi に残す」は「その他の設定」へ移った。implementer の文書の点検は `手前|奥|ヘッダー|マッチ` での `rg` で、これらは拾えなかった
- 起きる場面: CLAUDE.md の「マージ後に確かめること」で docs/raspi.md を見て確かめるとき。`tools/pi_ui_check.py:130` のコメント
  「「解析の設定」の下」も同じく古い

## 検討

### 4. `/analyze-photo` で `bottom_colour` を省略したとき、読み取りと呼び方が食い違う

- 場所: `analyzer/app.py:168`（`int | None = Form(None)`）、`:196`（`bottom_colour or 0`）、`:83`（`names_ja(bottom_colour != 0)`）
- 何が問題か: 省略すると読み取りは `0`（手前＝暗い方の駒）で読むのに、summary では手前を「白」（明るい方）と呼ぶ。
  仕様 9 の「描かれた色で呼ぶ」と逆になる。README（`analyzer/README.md` の /analyze-photo）はこの食い違いをそのまま書いている
- 起きる場面: PWA は常に送る（`app.js:811`）、`tools/check_pi.py:79` も送るので、PWA と道具では起きない。API を直接叩いて
  省略したときだけ。`Form(0)` のままにすれば、省略時は読み取りも呼び方も「手前＝暗い方＝黒」で揃い、`| None` と `or 0` も要らない
  （ただし省略時の summary が「黒が有利」になる。どちらにするかは判断が要る）

### 5. 「その他の設定」に畳んだ、端末に残る設定のオンが見えなくなる

- 場所: `analyzer/static/index.html` の `details.panel.more`（`plies`・`collect`）。どちらも `stored(...)` で端末に残る（`app.js:67`・`:76`）
- 何が問題か: 一度「3手」や「Pi に残す」にすると、次からは閉じた中にあって、オンのままだと分からない。「Pi に残す」は
  解析のたびに写真を Pi に保存する設定で（CLAUDE.md の「変えないもの」の例外 1）、写真の選択の画面の
  「写真は…保存しません。」とも食い違ったまま気づきにくくなる（この食い違い自体は前からある）
- 起きる場面: 「Pi に残す」をオンにした端末で、以後の解析。3手は結果の注記「gnubg 3手読み」で分かるが、Pi に残すは画面のどこにも出ない
- 境界線上の判断なので報告だけ（仕様 4 は畳むことを指定している）

### 6. マッチを結果の画面で直したときの解析し直しが、届かないコードとして残っている

- 場所: `analyzer/static/app.js:525-530`（`setMatch` の `if (state.step === "outcome") analyze();` とコメント「on the result screen the
  position is analysed again at once」）、`analyzer/test_pwa.py` の `test_match_is_in_the_board_settings_and_sent`（この行があることを検査）
- 何が問題か: `#match` は盤面の画面（`#board` の section）に移り、結果の画面では隠れる（`[hidden] { display: none !important }`）ので
  `setMatch` は結果の画面から呼ばれない。README からは「結果の画面で変えると解析し直す」を消したのに、コードとテストは残っている
- 起きる場面: 実害は無い（呼ばれないだけ）。読む人が「結果の画面でも直せる」と誤解する

### 7. 新しい規則（ダブルされたところではダイスを使わない）を確かめるテストが無い

- 場所: `analyzer/static/app.js:84-87`（`diceIn`・`cubeOffered`・`rolled`）、`:833-835`（写真から読んだダイスで offered を外す）
- 何が問題か: implementer は Playwright で手で確かめたが、残るテストは無い。`test_pwa.py` は app.js を文字列で検査している
  所があり（`:73` など）、同じ程度の検査も無い。サーバー側も、`/analyze-photo` で `bottom_colour` が summary の名前に効くことの検査は無い
  （`test_api.py` は `/analyze` だけ）
- 起きる場面: 後の変更で `rolled` を `diceIn` に戻すなどしても落ちない。`tools/pi_ui_check.py` の `double`（PI-017）は写真から
  ダイスを読む側だけを見る

### 8. ルーペが、盤の上から始めたスクロールのたびに一瞬出る（未確認）

- 場所: `analyzer/static/board-view.js:139`（`pointerdown` で `showLoupe`）
- 何が問題か: タッチでは、ブラウザがスクロールと決めて `pointercancel` を出すまでの間、ルーペが出る。盤は画面の大きな部分を占める
- 起きる場面: スマホで盤の上に指を置いて縦にスクロールしたとき。実機・エミュレーションでの見え方は未確認。仕様 5 は
  `pointerdown` で出すと指定しているので、境界線上の判断として報告だけ

## 好みの範囲

### 9. 名前の span に `pointer-events: none` を付けるより、`.seg` のクリックを `closest("button")` で読む

- 場所: `analyzer/static/style.css:314`、`analyzer/static/app.js:1120`
- `#paint-side` は既に `e.target.closest("button")?.dataset.value`（`app.js:1045`）で読んでいる。`.seg` も同じにすれば CSS の回避は要らず、
  これから span を足しても壊れない

## 問題の無かった観点

- 1 ルーペとタップ・長押し・スクロール: `bindTap` の変更は `pointerdown` での `showLoupe` と `cancel` での `hideLoupe` だけで、
  `down`・`timer`・`fire` の流れは前と同じ。ルーペは `pointer-events: none` で `position: fixed`、指の上か下に `gap` 36px 離して置くので
  指の下に来ない。`#result-svg` は `pointer-events: none` で出ない。`svg.viewBox.baseVal` は `draw` が必ず設定する
- 2 ダブルされたところのダイス: `rolled()` が null を返すので、`/analyze` の body・`/analyze-photo` の `dice`・`inputsKey`・盤面図のダイス・
  `update()` の手番の決め方・`#onroll-label` のどれにも効かない。写真にダイスがあるときは、サーバーが `doubled=False` で解析し
  （`app.py:283-287`）、PWA が offered を外すので、`inputsKey` で作り直した要求（`BgCube.request`）とサーバーの解析が一致する。
  キューブが遊戯面のとき（field）はダイスを消すので外さない。履歴と精度改善用の書き出しは `diceIn` で、前の `rolled` と同じ値
- 3 名前（白・黒）: 画面（`.nm-white`/`.nm-black`、`#counts`、警告、`#cube-help`）・`result.js`（表・帯・文・読み上げ・`matchText`）・
  サーバーの summary（`/analyze` と `/analyze-photo` に PWA が `bottom_colour` を送る）は同じ規則（0 なら手前が黒、それ以外は白）。
  `inputsKey` に `bottomColour` があるので、色を変えると前の summary は古い扱いになる。省略時の食い違いは上の 4
- 4 hidden の切り替え: `#export-sample`・`#collect-opt`・`#collect-note`・`#claude-corners`・`#claude-note` は details の中でも同じ条件で
  切り替わる。`#errors`・`#home-note`・`#dice-note`・`#cube-note` は畳んだ所の外にある。警告で見えなくなったものは無い
  （閉じた中で見えないことの扱いは上の 5）
- 5 文章を削った所: 写真の選択の「写真はサーバーで読み取るだけで、保存しません。」は残っている。`#claude-note` は
  「写真が Anthropic に送られます」で、`#claude-corners` と同じ「その他」の中に並ぶ
- 6 `analyzer/README.md`: 下のバー、「その他」の中身、ホームの呼び方、ダイスを出さない条件、マッチの場所、`/analyze` の
  `bottom_colour`、`/analyze-photo` の省略時の扱いは、コードと合っている（省略時の扱いそのものは上の 4）
- 版: analyzer は `__version__`・`APP_VERSION` とも 0.52.0、`sw.js` は v56。recognizer は変えていないので上げていない（CLAUDE.md の「バージョン」どおり）
- 範囲: `tools/pi_ui_check.py:74` と `shots.py` の待ち方は、文言と画面の変化に合わせた直しで、範囲を外れた変更は見当たらない

## 作り込みすぎ

- `analyzer/app.py:168,196`: yagni: `bottom_colour: int | None = Form(None)` と `bottom_colour or 0` は、省略時に読み取りと呼び方を分けるためだけにある。`Form(0)` のまま渡せば 2 か所とも消える（上の 4。判断が要る）
- `analyzer/static/app.js:529`: delete: 結果の画面でマッチを直したときの `analyze()`。届かない（上の 6）。`test_pwa.py` の対応する検査も消せる
- `analyzer/static/style.css:314`: shrink: `.nm-white, .nm-black { pointer-events: none }`。`app.js:1120` を `e.target.closest("button")?.dataset.value` にすれば要らない（上の 9）

net: -4 lines possible.

## 直しの再レビュー

対象は implementer の報告の末尾 2 節（「レビューを受けて直したこと」「レビューの 6・7 を直したこと」）の分だけ。前に問題無しとした観点は見直していない。

### 指摘ごとの結果

- 1（閉じた details の中を道具が押せない）: 解消。`tools/pi_ui_check.py` の `reveal` と `tools/ui_snapshot.py` の `Run.reveal` は、閉じた祖先の `details` の `summary` を押してから押す。`seg`・`go` も `click` を通る。details の外の要素では `count()` が 0 で何もしない。manual の流れの直し（キューブを片側に置くとダイスの欄が隠れるので、`#cube-offered` を外してからダイスを消す）も、新しい画面の動きと合っている
- 2（`CRAWFORD_CUBE`）: 解消。「「ゲーム」のクロフォードを外してください。」で、`#match` のラベル「ゲーム」と合う
- 3（`docs/raspi.md`）: 解消。:128・:132・:182 と `pi_ui_check.py` のコメントが今の画面と合っている
- 4（`/analyze-photo` の `bottom_colour`）: 解消。`Form(0)` に戻り、読み取りと summary の呼び方が同じ値を使う。README の /analyze-photo も「既定 `0`。読み取りと…呼び方の両方に使う」に直っている
- 5（畳んだ設定のオンが見えない）: 解消。`#more-set` が「その他の設定（3手・Pi に残す）」のように添える。「Pi に残す」は `#collect-opt` が出ているときだけで、`/version` を受けた後に `redraw(drawMoreSet)` で描き直す（`part` のキーに DOM の hidden が入らないのを補っている）
- 6（届かない `analyze()`）: 解消。`setMatch` の分岐とコメント、`test_pwa.py` の対応する検査が消えている
- 7（テストが無い）: 解消。`test_no_dice_while_a_double_is_offered` は `node` が無いときの `skipif` 付きで、`usedDice`・`request`・`offered` を Node で動かして見る。app.js の 3 行は文字列の検査。implementer が「壊すと落ちる」ことを 2 通り確かめている
- 8（スクロールのたびにルーペ）: 解消（コードを読んだ範囲。実機での見え方は未確認）

### 直しで動きが変わっていないか

- ルーペの遅らせ（`board-view.js`）: タップ・長押し・スクロールの流れは前と同じ。`pointerdown` は `down` と長押しのタイマーを前と同じに置き、ルーペのタイマーを足しただけ。`pointerup`・`pointermove`（SLOP 超え）・`pointercancel`・`pointerleave`・長押し・`contextmenu` はどれも `cancel` を通り、`cancel` が `loupeTimer` も消すので、取り消した後にルーペが出ることはない。100ms 未満のタップではルーペは出ず、`fire` はそのまま。2 本目の指で `pointerdown` が重なったときにタイマーが上書きされるのは、長押しのタイマーと同じで前からある
- `cube.js` に移した規則: 前と同じ。前の `cubeOffered` は `s.cube.at !== "centre" && s.cube.offered`、今の `BgCube.offered` は `!!cube && cube.at !== "centre" && !!cube.offered` で、違いは cube が null のとき落ちないことと、真偽値に揃えることだけ。`rolled` は `usedDice(s.cube, diceIn(s))` で、前の `cubeOffered(s) ? null : diceIn(s)` と同じ値。`cubeOffered({ cube })`（app.js:840）も同じに動く

### 新しく気づいたこと（報告だけ）

- 好みの範囲: 省略したときの既定が、`/analyze`（`bottom_colour` 省略で white を「白」、`analyzer/README.md:147`）と `/analyze-photo`（既定 0 で white を「黒」、`:221`）で違う。どちらも README のとおりで、PWA と道具は常に送るので画面には出ない。境界線上なので報告だけ

作り込みすぎ: なし（前の 3 件のうち 2 件は直り、`.nm-*` の `pointer-events` は「やらない」と決まった）
