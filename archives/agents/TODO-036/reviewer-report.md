# TODO-036 レビュー（reviewer）

対象: `git diff 44e9ec1..HEAD`（84c70e6）。要修正 0 件、検討 2 件、好みの範囲 2 件。

## 検討

### 1. 共有に断られたあとのダウンロードが、Chrome に止められるおそれ（実害は未確認）

- **場所:** `analyzer/static/app.js:1313-1328`
- **内容:** `navigator.share` は呼んだ時点でユーザーの操作（transient activation）を使い切る。
  断られたあとの `a.click()` は、操作が切れた状態での 2 件のダウンロードになる。
  `<a download>` のクリック自体は操作が無くても動くが、Chrome は 1 回の操作で 2 件目以降のダウンロードに
  「複数のファイルのダウンロード」の許可を求めることがある（DownloadRequestLimiter）。Android の Chrome で
  2 件目だけ止まる・許可の確認が出る、という形になりうる。
- **根拠:** 未確認。Pi の Chromium（Linux）には Web Share が無く、本物の share で操作を使い切らせて試せない。
  `export-denied` の `SHARE_DENIED` はすぐ reject するだけで操作を使い切らないので、この確認では捕まらない
  （Playwright の `evaluate` の中では `navigator.userActivation.isActive` が true だった）。
  PC の経路（共有が無いとき）も同じ 2 件のダウンロードだが、こちらは操作が残ったまま。
  PI-018 のスマホの行（Android の Chrome で 2 つがダウンロードされる）で確かめることになる。
  2 件とも落ちた、1 件だけ落ちた、を見分けて書いてもらうと、次の手が決めやすい。

### 2. 断られたうえにダウンロードも止められたとき、何も表示されない

- **場所:** `analyzer/static/app.js:1318-1320`
- **内容:** AbortError 以外のエラーはすべて握りつぶしてダウンロードへ進む。上の 1 が起きた場合、
  以前は「書き出せませんでした: …」が出ていたのが、何も出ない（ダウンロードの失敗は JS から見えない）。
  NotAllowedError 以外（例: TypeError、DataError）でもダウンロードに切り替わるのは、狙いどおりなら問題ない。
- **根拠:** コードを読んだ。実害は 1 が起きるかしだい（未確認）。

## 好みの範囲

### 3. `export-denied` が、共有を通ったことと alert が出ないことを見ていない

- **場所:** `tools/pi_ui_check.py:88-108`, `:148-149`
- **内容:** `ok` は `page.alerts` を見ない。共有を呼ばずにダウンロードする実装に変わっても `export-denied` は通る。
  今の差分を壊すと落ちるか、については、直す前の app.js（`throw err` → alert、ダウンロード 0 件）なら
  `len(files) == 2` で FAIL になるので、狙いの不具合は捕まえられる（静的に読んだ。走らせての確認は verifier）。

### 4. コメントが見立てを事実として書いている

- **場所:** `analyzer/static/app.js:1319`
- **内容:** 「Chrome on Android refuses a .json (NotAllowedError "Permission denied")」は TODO-036 では
  「と見ている」段階。PI-018 で確かめるまでは推測。切り替えは AbortError 以外すべてなので、挙動には影響しない。

## 問題ない観点

- 分岐の意味: 成功 → return、AbortError → return、その他 → ダウンロード。共有が成功してダウンロードもする二重の動きは無い。`canShare` が無い・false のときは従来どおりダウンロード。
- init script の順序: Playwright の文書は複数の init script の評価順を保証しないが、結果は順序によらない。`SHARE_DENIED` はインスタンスに自前のプロパティを作り、`INIT` は prototype を消すだけなので、どちらの順でも `navigator.share` は reject する関数になる（Pi の /usr/bin/chromium で両方の順を実測: どちらも `typeof navigator.share === "function"`、`Object.hasOwn(navigator, "share") === true`、`'share' in Navigator.prototype === false`、呼ぶと `NotAllowedError`）。
- 版: analyzer のコードを直す修正なので 0.25.2 → 0.25.3、`APP_VERSION` も同じ、`sw.js` のキャッシュ名も v31 → v32（前回 18884bf と同じやり方）。recognizer は変わっていないので上げない。CLAUDE.md の「バージョン」どおり。
- docs/PI_CHECKS.md: 「残っている項目」に PI-018、次の番号 PI-019、件数 16 は決着していないので据え置きで正しい。PI-018 は PI-014 の上（新しい番号ほど上）。担当・足した日・確かめ方・期待・Pi とスマホの行が揃っている（「足した日・PR」に PR 番号はまだ無い。PR を作ったら足す）。表に `export-denied` を足し、「画面の操作が要る項目を足したら、ここにも確認を足す」にも合う。
- TODO.md: 実装の時点でチェックを入れていて、規則どおり。
- 文書との整合: analyzer/README.md:57 の「JSON を共有できない Android の Chrome … では 2 つともダウンロードになる」は、この修正で実装と合うようになった。他に古くなった記述は見つからなかった（`rg -e 書き出 -e ダウンロード -e pi_ui_check -e NotAllowedError`）。
- 範囲: 指示に無い変更は無い。
- 規約（CLAUDE.md の変えないもの）: 触れていない。

## 作り込みすぎ

作り込みすぎ: なし（`open_app` / `check_export` の `*scripts` は使い手が 1 つだが、2 行の差で済んでいる）。
