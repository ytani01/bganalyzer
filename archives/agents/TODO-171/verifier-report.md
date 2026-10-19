# TODO-171 verifier の報告

worktree: `.claude/worktrees/impl-171`（HEAD 0ca6cb4）。コードは直していない。

## 1. 一致の件数（一致）

`uv run python archives/agents/TODO-171/check_guess.py samples/*.truth.json ~/work/bganalyzer/collected/*.truth.json`（終了コード 0）。
引数なしでは 0 組になる。143 組 = samples 87 組 + トップの `collected/` 56 組（worktree には `collected/` が無いので、トップのものを渡した。`samples/external` の 8 組は入らない）。

```
143 組 × 4 通り = 572
  色だけ（home は正解のまま）: 572
  A（色 → home）: 546  B（home → 色）: 546  A で同点: 20
```

- 報告どおり: 546/572、同点 20、手前の色だけなら 572/572（全組一致）。
- 不一致の組は 9（`不一致` の行を数えた）。samples の 4 組（collected-blue-felt-oblique、collected-cream-far、collected-red-blue-far、commons-case-dice）と collected の 5 組（user-…-dplmij、…-wcfrvo、…-kuetnz、…-r0woj7、…-z0r1g8）。報告の「外れが 9 組」と件数は同じ。名前の突き合わせは、報告が挙げた 3 組（blue-felt-oblique、cream-far、wcfrvo）と kuetnz だけ出てきた（ほかの名前は報告に無い）。

## 2. CLI の `--bottom-colour auto --home auto`（一致）

四隅・正解は `samples/*.truth.json` から。`uv run python recognizer/board.py samples/<写真> --corners … --home auto --bottom-colour auto`（2 組とも終了コード 0）。

| 組 | 正解の bottom_colour / home | 推測した bottom_colour | colour_guess.pips（[色 0 を手前, 色 1 を手前]） | 推測した home / margin |
|---|---|---|---|---|
| collected-app-green-far（手前が明るい） | 1 / right | **1** | [431, 215] | right / 12.7 |
| collected-app-green-shot（手前が暗い） | 0 / left | **0** | [249, 417] | left / -12.8 |

2 組とも色・home が正解と同じ。

## 3. 既定の動き（auto にしない）と origin/main の比較（一致）

origin/main の `recognizer/` を `git archive` で scratchpad に出して（worktree は使っていない）、同じ引数（`--home <正解> --bottom-colour <正解>`）で 2 組を流した。
アスキーの盤面は 2 組とも同じ。JSON は info に `bottom_colour`（正解の値）と `colour_guess`（null）が**増えただけ**で、ほかのキーの値は全部同じ（再帰で比べた）。

## 4. 版と README

- 版: recognizer 0.29.0（main 0.28.0）、analyzer 0.93.0、`APP_VERSION` 0.93.0 — 3 つ揃っている。
- `recognizer/README.md` の `--bottom-colour auto`（ピップ数が少ない側、home より先、同点は明るい方、アプリは新しい写真で auto）は実装と合う。`board.py` の choices に `auto` あり、`--home auto` のとき色ごとに左右の少ない方、は `colour_guess` の値と矛盾しない（2 の実測）。
- `analyzer/README.md` の `colour_guess.pips` の並び（暗い方 → 明るい方）は、2 の実測（暗い手前の組で [249, 417]、明るい手前の組で [431, 215]）と合う。
- 「手で盤面を作るときは直前の写真の色、写真が無いときは端末に覚えた色」の文は、実装の報告の説明と同じ。**app.js の動きは読んでいない・実際に動かしていない**（PWA の操作は依頼の範囲外）。

## 変更ファイル

`git diff origin/main...HEAD --stat`: TODO.md、analyzer/{README.md,app.py,static/app.js,test_api.py,test_pwa.py}、recognizer/{README.md,board.py}、archives/agents/TODO-171/{check_guess.py,implementer-report.md,reviewer-report.md}。依頼の範囲内。
未追跡: `archives/agents/TODO-171/reviewer-report-2.md`（まだコミットされていない）。

## 気づいた点（実害は未確認）

- ブランチは origin/main より 6 コミット遅れている（`rev-list` で 6 / 5）。origin/main の `analyzer/app.py` は 0.92.2 で、この PR の起点は 0.92.1。マージの前に main を取り込むときに版の競合が出るかもしれない（実害は未確認。判断は管理者）。
- 実装の報告は「0.92.1 → 0.93.0」と書いてあり、origin/main は 0.92.2。

## 確かめなかったこと

テスト全体、全サンプルの認識、PWA の画面、`app.js` の動作、reviewer が見た観点の読み直し。
