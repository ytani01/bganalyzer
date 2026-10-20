# TODO-180 implementer の報告

## 変更点

- `.github/workflows/test.yml:4-8`・`ruff.yml:4-8`・`accuracy.yml:9-11`: push の起動条件を `branches: [main, 'claude/**']` に。`accuracy` の push の paths、各 pull_request の paths の絞り込みは保った。PR の起動条件も残した（自動の取り込み PR 用）。
- `CLAUDE.md`: 「共同開発」の worktree 節（取り込み後の `git pull`、担当の作業内容、片付けに origin のブランチ削除を追加）、PR の節を「変更は PR なしで main に取り込む」に差し替え（push → `gh run watch` で待つ → rebase → トップで `git merge --ff-only` → `git push origin main` → 片付けの 5 手順、CI の待ち方の 1 行を含む）、CI の条件の節を書き直し。ほかに「PR」「マージ」を前提にした語（「バージョン」「精度の確認」「取り込み後に確かめること」の見出しと本文、盤の外の公開の節）を直した。`import_collected.py` の自動 PR の記述（`CLAUDE.md:51`）は残した。
- `docs/HANDOVER.md`: 運用の行、招待の説明、プロジェクト指示（共同開発の相手も同じやり方と明記）、CI の説明、ぶつからないための決まりを直した。行 18・24・116 など過去の経緯の PR は直していない。
- `docs/raspi.md`: 取り込み後の確認の語、`samples/` の公開の節、しきい値を試す節の語を直した。自動の取り込みの PR の記述は残した。
- `recognizer/README.md:73,514`: CI の起動条件と「採るなら」の語。
- `TODO.md:77-79`: 3 つのチェックを入れた。`- [ ] ローカル:` は残した。

## 検証

- `yaml.safe_load` でワークフロー 3 本が読めることだけ確認（終了コード 0）。実際に CI が走るかは verifier が、この項目自身の push で確かめる。
- 洗い出し `rg -n -e '\bPR\b' -e 'gh pr' -e 'マージ' …` の残りは、自動の取り込み PR の記述・過去の経緯・フックの文言のみ。

## 判断が要る点・残る懸念

- **`.claude/hooks/no-local-pytest.py:26` の文言「（gh pr checks）」は直せていない。** `.claude/` の編集が自動のチェックに拒否された（Self-Modification）。「（push したあと gh run watch）」に直したい。管理者が直すか許可を。
- `test`・`ruff` の push に paths の絞り込みが無いので、文書だけの変更でも `claude/**` への push で走る（main への push が元から毎回走るのと同じ）。CLAUDE.md にもそう書いた。絞るなら paths-ignore を push にも付けるが、main の push が文書だけで走らなくなる。
- 自動の取り込みのブランチ名が `claude/collected-import-*` なので、push と PR の両方で CI が走る（二重に走る。害は無いが時間は増える）。
- 取り込み（`git merge --ff-only` のトップ）が、トップの post-merge のサービス再起動を起こす点は今までの `git pull` と同じ。
- 「CI の待ち方（`gh run watch`）」は CLAUDE.md に書いた（2026-10-20 ユーザー決定）。
