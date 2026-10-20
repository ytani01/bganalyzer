# TODO-180 verifier 報告

CLAUDE.md「共同開発」の手順を、この項目自身の取り込みで実行した。コードと文書は直していない。

## 結果

| 手順 | 結果 |
|---|---|
| 1. `claude/todo-180-ff-merge`（0f6b248）を push | `ruff` 39374315454 / `accuracy` 39374315538 / `test` 39374315723 の 3 つが走り、`gh run watch <ID> --exit-status` はすべて exit=0（success）。3 つとも走ったのは、差分に `.py`・`.github/workflows/*.yml`・`recognizer/README.md` が入っているため（accuracy は `recognizer/**` と自身の yml）。手順どおり、run は push の約 8 秒後に引けた |
| 2. force push と paths | 下記 |
| 3. 取り込み | トップ（main）は origin/main（67a4b5a）と同じ。`git merge --ff-only` が通り、`git push origin main` が成功（67a4b5a..0f6b248）。origin の `claude/todo-180-ff-merge` を削除した。post-merge が「bganalyzer を再起動した」と出し、`systemctl --user is-active bganalyzer` は active |
| 4. ローカル | `curl localhost:8000/version` → `{"analyzer":"0.94.3","recognizer":"0.29.3","commit":"0f6b248",...}`。トップの HEAD = origin/main = 0f6b248、`git status` は clean。TODO.md の `- [ ] ローカル:` の行（main が最新になること）は満たしている。TODO.md はチェックしていない |

## 2. force push と paths（捨てるブランチ `claude/todo-180-fp-test`、1 回ずつ）

| push | 結果 |
|---|---|
| 0f6b248 と同じ commit から新しいブランチを push | run なし（40 秒待っても `gh run list --branch` が空）。新しい commit が無いため |
| `git commit --amend`（メッセージだけ変更、木は同じ）→ `--force-with-lease`（0f6b248 → 007a114） | run なし（30 秒待った）。**paths の絞り込みで飛ばされる**（変更ファイルが 0 件） |
| amend し直して `tools/check_pi.py` に 1 行足した commit を載せて `--force-with-lease`（007a114 → 72b4dd5） | `test` 39374731402 と `ruff` 39374731388 が走った。`accuracy` は走らず（`tools/` は accuracy の paths の外なので期待どおり） |

後始末: 上の 2 つの run は cancel した。origin とローカルの `claude/todo-180-fp-test` を削除した。`git ls-remote --heads origin 'claude/todo-180*'` は空。

## 手順どおりにいかなかった点

なし。ただし、次は CLAUDE.md の手順に書かれていない挙動として観察した（手順が通らないわけではない）。

- rebase で変更が無くなった（amend のみ・差分 0 件）push は、force push しても CI が走らない。手順 3 で main に追いついていないだけの rebase だと、**走らないことがある**。その場合 `gh run list --commit $(git rev-parse HEAD)` が空のままになるが、CLAUDE.md の「空のまま取り込まない」を字義どおり読むと、取り込めなくなる。（この場合は直前の run で見た木と同じなので実害は無いはず。実害は未確認。書き方を直すかは管理者の判断）
- 手順 4 で main に push すると、main への push でも `test`・`accuracy`・`ruff` が走る（39374785826 / 39374785827 / 39374785911、確認時は queued）。これらの結果は見ていない。

## 確かめなかったこと

- 手順 3 の「ff-only にならないとき」「push が拒否されたとき」の分岐（今回は起きなかった）。
- main への push で走った 3 つの run の結果。
