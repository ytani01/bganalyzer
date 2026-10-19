# TODO-146 reviewer の報告

対象: `git diff main...HEAD`（claude/collected-remove-imported、85de633）。
`uv run pytest analyzer/test_collected.py` は 10 passed。

要修正: なし

## 検討

### 1. テストが、消すかどうかの判断と「マージに失敗したとき偽を返す」を押さえていない
- 場所: `analyzer/test_collected.py:169-203`、`recognizer/import_collected.py:193-195`・`229`
- 内容: 作業用のコピー（scratchpad の `git archive` を書き換えたもの）で次の 4 つを壊して、
  `-k "removes or merges"` を流した。
  | 壊したところ | 結果 |
  |---|---|
  | `remove()` の glob を `stem + "*"` にする | 落ちる（よい） |
  | `merge()` の最後を `return True` にする | **通る** |
  | `_run()` の `if merge(...)` を `if merge(...) or True` にする | **通る** |
  | `update-branch` が失敗したときの `return log(...)` を `return True or ...` にする | **通る** |
- 根拠: 失敗のテストは `checks` が落ちる道だけを通り、`gh pr merge` が非 0 を返す道（`merged.returncode != 0`）と
  `update-branch` が落ちる道は通らない。`_run()` にはテストが無く、マージに失敗しても消す、という壊れ方を捕まえられない。
  この項目で一番困る壊れ方（PR が開いたままなのに collected/ から消える）が、どのテストでも落ちない。
- 足すなら、`failing` と同じ形で `merge` が `R(code=1)` を返す場合の `assert not merge(...)` が 1 行で済む。
  `_run()` の配線（merge が偽なら remove を呼ばない）は git・gh を全部差し替えることになり重い。そこまで要るかは管理者の判断。

### 2. 消したあとも、開発機の `collected/report.md` に消した組が残る
- 場所: `recognizer/collected.py:89-93`（差分の外）と `recognizer/import_collected.py:194`
- 内容: `measure()` は `report.md` と `.measured.json` を書いたあとで `to_samples()` を呼ぶので、
  取り込んで消した組が「読み違いのある組」として `report.md` に載ったまま、次に測り直すまで（新しい組が 10 たまるまで）残る。
  `.measured.json` に残る名前は `new_pairs()` が集合として見るだけなので害は無い。
- 根拠: 読んだコード。docs/raspi.md は「認識を直すのは… collected の report を見て直して」と書いており、
  開発機でそう頼むと、もう無い組を探しに行く。実害は未確認（開発機で report を読ませる運用があるかは知らない）。

## 好みの範囲

### 3. 写真と正解を消す処理が 2 か所にある
- 場所: `recognizer/import_collected.py:201-205` と `recognizer/collected.py:77-79`
- 内容: 同じ glob と unlink。`remove()` を `collected.py` に置いて、`measure()` もそれを呼べば 1 か所で済む
  （`import_collected` が `collected` を import しても、`collected` は重い import を関数の中でしかしないので軽い）。
  名前の決まり（`NAME`）が変わったときに片方だけ直す心配が減る。

### 4. 消すことを書いていない説明が 2 か所
- 場所: `analyzer/README.md:290`、`recognizer/README.md:785`、`docs/raspi.md:207`（mermaid の F）
- 内容: どれも「PR をマージまで進める」で止まっており、マージ後に collected/ から消すことに触れていない。
  食い違い（誤り）ではなく、書いていないだけ。docs/raspi.md の 210 行・218 行の書き足しは実装と合っている。

## 問題なしの観点

- `merge()` の戻り値: 途中の `return log(...)` は `log` が `print`（テストでは `list.append`）の戻り値 `None` を返すので偽。真になるのは `gh pr merge` が 0 を返したときだけ。
- `remove()` の glob: `NAME` が `[A-Za-z0-9-]` だけなので、組の名前に `.` も glob の特殊文字も入らない。`stem + ".*"` は `user-1-aaa` で `user-1-aaab.*` を拾わない（テストと壊した版で確認）。`report.md`・`import.log`・`.measured.json` も拾わない。
- 消すタイミング: `remove()` は `try` の中で `finally`（worktree の片付け）より前。消すのは `collected/` の元の組（`todo`）で worktree の中ではないので、片付けとぶつからない。マージ後・消す前に SIGTERM で止まっても組が残るだけで、次は `pick()` が id で除くので取り込み直さない。`remove()` が例外を出しても `finally` は走り、`run()` が `import.log` に `failed` を残す。
- 決まっていること: CI 落ち・PR が開いたままでは消さない／別 id の送り直しを見分けない／既存の 36 組に手を付けない、のどれにも反していない。
- 規約: バージョンは測る道具の変更なので上げていない（CLAUDE.md の「バージョン」どおり）。行長・書き方は周りに揃っている。
- 範囲: 指示に無い変更は無い。TODO.md のチェックは実装した時点で入っている。
- コメント: docstring の追加は「何を返すか」で、モジュール冒頭の追記は TODO 番号付きで周りと揃っている。

## 作り込みすぎ

- `import_collected.py:L201-205` + `collected.py:L77-79`: shrink: 同じ glob/unlink が 2 か所。`collected.remove()` 1 つにして両方から呼ぶ（上の 3）。

net: -3 lines possible.
