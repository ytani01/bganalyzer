# TODO-077 確認報告（verifier）

対象: ブランチ `claude/todo-077-black-on-black`、HEAD `f98a579`。コードは変更していない。

## 手順 1: 5 サンプルの evaluate.py

コマンド: `cd recognizer && uv run -q python evaluate.py ../samples/{photo5,commons-tavli-black,commons-dark-homeleft,commons-leather-cups,collected-l9azfe}.truth.json`（終了コード 0）

出力（points の行のみ抜粋。他の項目は省略せず引用）:

```
photo5.truth.json: 24/24 points correct, bar ok, home guess wrong (+16.5), dice not read (read None, truth [6, 2]), cube ok (read None, truth centre)
commons-tavli-black.truth.json: 24/24 points correct, bar ok, home guess ok (+17.7), dice ok (read [6, 1], truth [6, 1]), cube ok (read None, truth None)
commons-dark-homeleft.truth.json: 24/24 points correct, bar ok, home guess ok (-17.7), dice ok (read None, truth None), cube ok (read None, truth None)
commons-leather-cups.truth.json: 15/24 points correct, bar ok, home guess ok (-0.5), dice WRONG (read [3, 3], truth None), cube ok (read None, truth None)
   point  7: truth +0  got +3
   point  8: truth +3  got +0
   point 12: truth -5  got +0
   point 13: truth +5  got +0
   point 14: truth +0  got +5
   point 15: truth +0  got -1
   point 17: truth -3  got +0
   point 19: truth -5  got -2
   point 22: truth +0  got -1
collected-l9azfe.truth.json: 18/24 points correct, bar ok, home guess ok (-24.3), dice ok (read None, truth None), cube ok (read None, truth centre)
   point  3: truth +2  got +3
   point  6: truth +2  got +3
   point 12: truth -5  got -6
   point 13: truth +5  got +6
   point 15: truth -1  got +2
   point 19: truth -5  got -6
```

判定:
- photo5 24/24: 一致
- commons-tavli-black 24/24: 一致
- commons-dark-homeleft 24/24: 一致
- commons-leather-cups 15/24: 一致
- collected-l9azfe 18/24: 一致

補足: photo5 の「home guess wrong (+16.5)」は、期待値の一覧には無い項目で、点数の判定には影響しない。この項目は今回の確認の対象外として、食い違いには数えていない。

## 手順 2: photo5 で TEX_MIN_COVERED = 99

コマンド: `checkers.TEX_MIN_COVERED = 99` のあと `evaluate.run('../samples/photo5.truth.json')`（終了コード 0）

出力:

```
22 [(1, -2, 0), (6, -2, 0)]
```

判定: 一致（期待 22。point 1 と 6 が外れる）。出力の tuple の並びを (point, truth, got) と読んだ。これは出力の形からの読みで、`evaluate.py` の中身は読んでいない。

## 手順 3: commons-leather-cups で TEX_MIN_COVERED = 3.0

コマンド: `checkers.TEX_MIN_COVERED = 3.0` のあと `evaluate.run('../samples/commons-leather-cups.truth.json')`（終了コード 0）

出力:

```
14 [(7, 0, 3), (8, 3, 0), (11, 0, -4), (12, -5, 0), (13, 5, 0), (14, 0, 5), (15, 0, -1), (17, -3, 0), (19, -5, -2), (22, 0, -1)]
```

判定: 一致（期待 14。point 11 に -4 が出ている）。

## 変更ファイルと指示の範囲

`git diff --stat main...HEAD`（7 ファイル、39 行追加・10 行削除）:

- `recognizer/checkers.py`: 指示の変更そのもの（TEX_MIN_COVERED の追加、上位 25% の基準、continue の整理）。範囲内。
- `recognizer/board.py`: `__version__` 0.23.0 → 0.23.1。recognizer の読み取りが変わるため、CLAUDE.md の版上げに沿う。
- `recognizer/accuracy_baseline.json`: photo5 の基準 22 → 24。サンプルの基準の書き直し。CLAUDE.md の「良くなったとき」に沿う。
- `recognizer/README.md`: 精度の表の photo5 行の更新。
- `recognizer/tune.py`: 調整するパラメータの一覧に `checkers.TEX_MIN_COVERED` を 1 つ足しただけ。指示には無いファイルだが、新しい定数の調整対象に加えたもの。
- `TODO.md`: 2 項目のチェックを入れた（`- [x]`）。CLAUDE.md の「実装できた時点で入れる」に沿う。
- `archives/agents/TODO-077/tex.py`: 新規。archives 配下の補助スクリプト。指示には無いファイル。内容は読んでいない。

作業ツリーの未追跡ファイルは `archives/agents/TODO-077/reviewer-report.md` が 1 つだけ。これはブランチの差分には入っていない。今回の確認では変更していない。

食い違い（指示の範囲との違い）: `archives/agents/TODO-077/tex.py` と `recognizer/tune.py` は、指示に列挙されていないファイルとして報告する。判断は管理者に任せる。

## 確認できなかったこと・判断できなかったこと

- 全サンプルの evaluate.py と check_accuracy.py は、指示どおり流していない。
- 手順 2・3 の出力の tuple の意味（(point, truth, got)）は、出力の形からの読みで、`evaluate.run` の中身は確かめていない。
- 手順 1 の photo5 の「home guess wrong」は、期待値に無いため判断していない。
- `tex.py` の中身と、`tune.py` の変更が指示の範囲に含めるべきかどうかは、判断していない。
