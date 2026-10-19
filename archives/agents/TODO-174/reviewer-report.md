# TODO-174 reviewer 報告（PR #512、`git diff origin/main...HEAD`）

要修正: 0 件

## 検討

### 1. `analyzer/test_api.py:269` / gitdir が相対パスの場合をテストが見ていない
- テストの `.git` ファイルは絶対パス（`gitdir: {wt_git}`）だけ。`analyzer/app.py:141-145` の基点を
  `git_dir.parent` から `Path.cwd()` に壊しても、`-k git_commit` は 2 passed のまま（実測）。
- 実装そのものは相対パスでも読める: `git worktree add --relative-paths` で作った worktree
  （`.git` は `gitdir: ../m/.git/worktrees/wr`）で `git_commit()` は `git rev-parse --short=7` と同じ `347d7af` を返した（実測、git 2.56.0）。
- 基点を壊すと落ちるようにするなら、相対パスの `.git` を 1 つ足す。実害は未確認（今の worktree は絶対パスで作られている）。

### 2. `analyzer/app.py:144` / `.git` ファイルが UTF-8 でないと `UnicodeDecodeError` が外へ出る
- `except (OSError, StopIteration)` は `UnicodeDecodeError`（`ValueError` の仲間）を拾わない。
  `.git` に `b"\xff\xfe"` を書くと例外が出た（実測）。`git_commit()` は lifespan（`app.py:62`）で呼ばれるので、起動が止まる。
- `HEAD` を `read_text()` で読む元のコードにも同じ性質があり、今回の差分で新しく入った種類ではない。読む入口（`.git` ファイル）が 1 つ増えただけ。実害は未確認（git が書くファイルなので、普通は起きない）。

## 問題が無かった観点
- 普通の `.git` ディレクトリ: `is_file()` が偽、`commondir` が無いので `common = git_dir`。loose → packed の順も元と同じ（読んで確認。既存テストも通る）。
- 絶対・相対の gitdir、本体の packed-refs だけにある ref、detached HEAD: 本物の git worktree で全て正しい ID（実測）。
- `commondir` が無い・中身が壊れた `.git`（`garbage`、空）: None を返す（実測）。
- git コマンドに頼っていない（ファイルだけ読む）。
- テストの強さ: commondir を無視する／loose を gitdir だけで探す／packed-refs を gitdir から読む／worktree の分岐を消す、の 4 つは、どれも 1 failed（実測。終わった後に `git checkout` で戻し、`git status` が空なのを確かめた）。
- 版: analyzer 0.92.1 → 0.92.2（patch）、`APP_VERSION` も揃っている。#510 とぶつかる件は指摘しない（依頼どおり）。
- 範囲・規約・コメント: 指示外の変更なし。コメントは「なぜ」（worktree の `.git` はファイル、refs は本体にある）。文書に古い記述なし（`rg gitdir|commondir|git_commit`）。
- 作り込みすぎ: なし。
