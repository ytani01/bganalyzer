# TODO-174 verifier 報告（PR #512、worktree impl-174、HEAD c4d3796）

コードは直していない。境界線上の判断はしていない。

## 結果
1. `uv run pytest analyzer/test_api.py -v`（1 回）: **53 passed**、終了コード 0（86.56 秒）。
   - `test_version_reports_both_parts_and_commit` PASSED
   - worktree 関係: `test_git_commit_follows_a_worktree` PASSED、`test_git_commit_reads_packed_and_detached_refs` PASSED
2. worktree で `app.git_commit()` = `c4d3796`、`git rev-parse --short HEAD` = `c4d3796`。一致。
3. `git_commit(Path("/home/ytani/work/bganalyzer/.git"))` = `5a4585e`、`git -C ~/work/bganalyzer rev-parse --short HEAD` = `5a4585e`。一致。
4. 版: `analyzer/app.py` `__version__ = "0.92.2"`、`analyzer/static/app.js` `APP_VERSION = "0.92.2"`。一致。

## 件数が増えていない理由（食い違い）
- 実装の担当の「テストを足す前も後も 53 件」は**当たっていない**。テスト関数の数は `origin/main` の `analyzer/test_api.py` が 52、worktree が 53 で、**1 件増えている**（`test_git_commit_follows_a_worktree`。差分で確認）。
- 足す前の 53 件がどこから出たかは分からない（足す前の件数は自分では流していない。`origin/main` の関数の数え上げだけ）。実害は未確認。

## 範囲
`git diff origin/main --stat`: TODO.md、analyzer/app.py、analyzer/static/app.js、analyzer/test_api.py、archives/agents/TODO-174/ の報告 2 つ。指示に無いファイルの変更なし（verifier の報告を足す前の時点）。

## 確かめなかったこと
- 変更前の `git_commit()` が worktree で None を返すこと（コードを読んだだけ。`.git` がファイルなので `HEAD` を読めない）。実際には動かしていない。
- テストを壊して落ちるかは reviewer と実装の担当の実測に任せた（読み直していない）。
