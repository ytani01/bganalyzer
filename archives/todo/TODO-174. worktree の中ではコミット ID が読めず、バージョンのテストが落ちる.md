# TODO-174. worktree の中ではコミット ID が読めず、バージョンのテストが落ちる

|      | main | 担当 |
|------|------|------|
| 見込み | Sonnet 5.5 / effort medium | implementer（Sonnet 5.5）+ reviewer（Opus 5.5 / medium）+ verifier（Sonnet 5.5）。分岐が変わるので reviewer を入れ、先に回す |
| 実施 | Sonnet 5.5 / effort medium | implementer（Sonnet 5.5）+ reviewer（Opus 5.5 / medium）+ verifier（Sonnet 5.5） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main（立てる前後の会話） | Opus 5.5 / Sonnet 5.5 | medium | 192 | 47,233 | 148,955 | 6,824,940 | 100% |
| 合計 |  |  | 192 | 47,233 | 148,955 | 6,824,940 | 計 7,021,320 |

- `token-usage.py` は、立てたコミットから現在時刻までの会話ログを数える。implementer・reviewer・verifier の会話は別に数えられず、上の値に含まれていない可能性がある（実際に動いた担当別の量は分からない）
- 実際の担当の effort は、見込みから変えていない

## きっかけ

`analyzer/app.py` の `git_commit()` は `.git` をディレクトリとして読む。worktree では `.git` が `gitdir: …` と書いたファイルなので None を返し、`analyzer/test_api.py` の `test_version_reports_both_parts_and_commit` が落ちた。アプリの `/version` も worktree で起動するとコミット ID が出なかった（TODO-171 の実装中に見つかった）。

## やったこと

- `analyzer/app.py` の `git_commit()`: `.git` がファイルなら `gitdir:` をたどる（相対パスは `.git` のあるディレクトリが基点）。`commondir` があれば、ref を worktree の gitdir → 本体の .git の loose ref → 本体の packed-refs の順に読む。git コマンドには頼らない。HEAD が文字列でないときも `UnicodeDecodeError` で止まらず None を返す
- analyzer の版を 0.92.1 → 0.92.2、`analyzer/static/app.js` の `APP_VERSION` も揃えた
- `analyzer/test_api.py`: `test_git_commit_follows_a_worktree` を足した（絶対・相対の gitdir、本体の packed-refs、loose ref、detached、文字列でない HEAD）

## 確かめたこと

- worktree の中で `analyzer/test_api.py` が 53 件通った（`test_version_reports_both_parts_and_commit` を含む）。`ruff check`・`ruff format --check` も通った
- worktree と本体で、`git_commit()` の値が `git rev-parse --short` と一致した
- reviewer が、commondir の無視・loose を gitdir だけで探す・packed-refs を gitdir から読む・worktree の分岐を消す、の 4 つを壊してテストが落ちることを確かめた。相対 gitdir の基点を壊したときも落ちる（実装の担当が確認）

## 分担の振り返り

- reviewer が、相対 gitdir がテストで見られていないことと、`.git` の中身が UTF-8 でないときに起動が止まることを見つけた。どちらも実装の担当は気づいていなかった
- verifier が、実装の担当の報告にあった「テストの件数が増えていない」が誤りで、実際は 1 件増えていることを見つけた
- 次に同じ規模なら、reviewer と verifier を 1 人にまとめても足りそう。ただし reviewer の 2 件はテストを壊して実測しないと見つからなかったので、reviewer は残す
