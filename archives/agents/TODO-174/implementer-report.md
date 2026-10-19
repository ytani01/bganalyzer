# TODO-174 implementer 報告

## 変更
- `analyzer/app.py` の `git_commit()`: `.git` がファイルなら `gitdir:` をたどる。`commondir` があれば、ref を worktree の gitdir → 本体の .git の loose ref → 本体の packed-refs の順に読む。git コマンドは使わない。
- `analyzer/app.py` の `__version__` と `analyzer/static/app.js` の `APP_VERSION` を 0.92.1 → 0.92.2。
- `analyzer/test_api.py`: `test_git_commit_follows_a_worktree` を追加（一時ディレクトリに `.git` のファイル・gitdir・commondir を作り、packed-refs・loose ref・detached を確かめる）。
- `TODO.md`: TODO-174 のチェックボックス 3 つを入れた。

## 検証（worktree `.claude/worktrees/impl-174` の中）
- `uv run pytest analyzer/test_api.py -q`: 53 passed（`test_version_reports_both_parts_and_commit` を含む）
- `uv run ruff check`: 通った / `uv run ruff format --check`: 通った

## 残る懸念
- PR #510（未マージ）が analyzer を 0.93.0 に上げている。#510 が先にマージされたら、この PR は rebase して 0.93.1 に直す必要がある（`app.py`・`app.js` の 2 か所がぶつかる）。
- 壊すと落ちるかは確認していない（reviewer / verifier に任せる）。
