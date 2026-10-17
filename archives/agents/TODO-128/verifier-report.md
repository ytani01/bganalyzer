# TODO-128 確認報告（verifier）

対象: branch `claude/todo-128-win-breakdown`、差分は `git diff main...HEAD`。

## 1. `uv run pytest -q analyzer/test_pwa.py`

- 結果: `26 passed, 1 warning in 1.76s`、終了コード 0。

## 2. テストが壊すと落ちるか（`analyzer/static/result.js` を一時的に書き換え）

各変更の後に `git checkout -- analyzer/static/result.js` で戻した。

- (a) `Math.max(0, Math.round(10 * f(p[c])) / 10)` を `Math.round(10 * f(p[c])) / 10` にした → 落ちた。
  `test_win_table_splits_gammons` が `'<td class="sub">シングル勝ち</td><td>50%</td><td>0%</td>'` の行で `AssertionError`（負の値が出る）。
- (b) `Math.round(10 * f(p[c])) / 10` を `f(p[c])` にした → 落ちた。
  同じテストが `'<td class="sub">ギャモン勝ち</td><td>29%</td><td>0.3%</td>'` の行で `AssertionError`（丸めが効かない）。
- (c) シングル勝ちの式 `q.win - q.gammon` を `q.win` にした → 落ちた。
  同じテストが最初の `'<td class="sub">シングル勝ち</td><td>50%</td><td>17%</td>'` の行で `AssertionError`。
- 出力の末尾はいずれも `1 failed, 25 deselected` だった。終了コードは zsh で `PIPESTATUS` の名前が違い記録できなかった。失敗は出力の `1 failed` で判定した。
- 終わった後の `git status --short` は空（clean）。

## 3. node で `R.html(...)` の表の行

入力: white `{win: 62.4, gammon: 18.7, backgammon: 1.2}`、black `{win: 37.6, gammon: 9.1, backgammon: 0.4}`。
`R.html` の出力の `<table>` 内の行を読んだ（`scratchpad/check_rows.js`）。

```
0  (ヘッダー)  白 / 黒
1  勝率                62.4% / 37.6%
2  class="sub" シングル勝ち        43.7% / 28.5%
3  class="sub" ギャモン勝ち        17.5% / 8.7%
4  class="sub" バックギャモン勝ち  1.2% / 0.4%
5  エクイティ          0.100 / -0.100
6  ピップ数            140 / 167
sub rows: 3
```

- 並びは「勝率 → シングル勝ち → ギャモン勝ち → バックギャモン勝ち → エクイティ → ピップ数」で合っている。
- class="sub" は 3 行に付いている。
- 足し算: white 43.7 + 17.5 + 1.2 = 62.4、black 28.5 + 8.7 + 0.4 = 37.6。どちらも勝率と一致する。

## 4. バージョン

- `analyzer/app.py`: `__version__ = "0.72.0"`
- `analyzer/static/app.js`: `const APP_VERSION = "0.72.0";`
- 一致している。

## 変更ファイル

`git diff --stat main...HEAD` の 8 ファイル（TODO.md、analyzer/README.md、analyzer/app.py、analyzer/static/app.js、analyzer/static/result.js、analyzer/static/style.css、analyzer/test_pwa.py、archives/agents/TODO-128/reviewer-report.md）。
TODO-128 の範囲（表・版・テスト・文書）から外れるものは見当たらない。
`analyzer/static/style.css` は `.sub` のスタイル（字下げ）の追加と見られる（中身は未確認。見た目の良し悪しは対象外）。

## 確かめられなかったこと・判断できなかったこと

- 画面の字下げの見た目は見ていない（対象外）。TODO.md の `- [ ] ローカル:` の確認は未実施。
- 負の値を 0 に丸める（`Math.max(0, …)`）は TODO-128 の本文には書かれていない。丸めの誤差で負になる場合への対処と読める。仕様の範囲内かどうかは判断していない（報告のみ）。
- 実際の解析結果（gnubg）の値で 3 行の和が勝率と合うかは見ていない。node に与えた値で確かめた。
