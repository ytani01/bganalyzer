# TODO-145 reviewer の報告

対象: `git -C /home/ytani/work/bganalyzer-145 diff main...HEAD`（64e5027）

## 要修正

### 1. 412px 幅で「元に戻す」が 2 行に折り返す
- `analyzer/static/style.css:203`（`.editor-row` から `flex-wrap: wrap` を外した）と `analyzer/static/index.html:141-142`
- 説明の文（13px で 1 行に収まらない長さ）と「元に戻す」が同じ flex の行に入ったため、両方が縮む。
  `#undo` には `white-space: nowrap` も `flex: none` も無いので、日本語の文字の間で折り返す。
- 根拠（実測）: style.css をそのまま読み込み、`main` > `#editor` > `.editor-row` だけを置いたページを
  system の Chromium（`/usr/bin/chromium`、Playwright）で 412×915 に開いて測った。
  `#undo` は幅 64px・高さ 48px・テキストの行数 2（`nowrap` にしたときの幅は 86px）。
  説明の文は幅 286px・高さ 39px（2 行）、`#editor` 全体の高さ 62px。
  実際のページ全体・スマホのフォントでは測っていない（実害の見え方は未確認。実測は別の担当）。
- 前例: 同じ理由で `#corner-reset { white-space: nowrap; }`（style.css:171）がある。

## 検討

### 2. ui_snapshot の手順から「長押し以外で変えた色が空のポイントに置かれる」場面が消えた
- `tools/ui_snapshot.py:191`（消した行）
- 消した行は「黒を選んでから空のポイントをタップすると黒が置かれる」、つまり `state.paintSide` が
  タップに使われることを記録していた唯一の手順。残りの手順では空のポイントへのタップは
  既定の白（`tap(1, 3)`）だけで、長押しで選んだ色（`app.js:1261` の `paintSide: p.side`）が
  次のタップに使われることを見る手順は無い。`paintSide` を参照するテストも `analyzer/test_*.py` に無い
  （`rg -n paintSide` で app.js の 4 か所だけ）。
- 置き換えの例: 空のポイントを長押しして黒を選び、別の空のポイントをタップしてから snap する。
- 後ろの手順の前提は変わらない: 消した行が触ったのはポイント 3 と `paintSide` だけで、後ろの手順は
  駒のあるポイント（18・19）、`number(5)`、長押しで白を選ぶ `pick(4, "white")`、バー、`#undo` 2 回
  （直前の 2 手を戻す）なので、ポイント 3 の駒や黒の `paintSide` に頼っていない。
  `#editor-title` のクリック（196 行）は span になっても長押しのメニューの外なので、そのまま通るはず（未確認）。

### 3. 版が TODO-144 のブランチとぶつかる
- `analyzer/app.py:33`、`analyzer/static/app.js:14`
- 0.79.0 → 0.80.0 は「機能の変更」で CLAUDE.md の「バージョン」に合い、`APP_VERSION` も揃っている。
  ただしまだマージされていない `claude/sheet-no-scroll`（TODO-144）が同じ行を 0.79.1 にしている。
  どちらが先に入っても同じ行で衝突し、144 が後なら 0.80.1 に上げ直す必要がある。どちらを先にするかは管理者の判断。

## 好みの範囲

### 4. `.editor-row button` のセレクタが要らなくなった
- `analyzer/static/style.css:142`
- `.editor-row` の中のボタンは `#undo` だけになり、`#undo` は `class="button"` を持つので `.button` で同じ指定が当たる。
  `.editor-row button` を消しても見た目は変わらないはず（未確認）。

## 問題の無い観点
- 消した要素の参照: `rg -n "paint-side|paintSide" --glob '!archives/**'` で、残りは `#palette-side` の `.paint-side` クラス
  （index.html:120）とその CSS、app.js の `state.paintSide` だけ。`#paint-side` の id を引く所は無い。tools/pi_ui_check.py にも無い。
- state.paintSide: 初期値 white（app.js:66）、タップで `paintSide: put`（580）、長押しのメニューで `paintSide: p.side`（1261）、
  長押しの初期色（574）。差分はどれにも触れておらず、`part` から `s.paintSide` を外しても描画で使う所は無い。
- 文書: analyzer/README.md:67 を直してあり、ほかに「置く色」「色のボタン」を書いた文書は無い（TODO.md を除く）。
- 範囲: 指示に無い変更は無い。
- 作り込みすぎ: 4 のセレクタ 1 つだけ（net: -1 セレクタ）。
