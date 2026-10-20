# TODO-180. worktree の変更を PR なしで main に取り込む

|      | main | 担当 |
|------|------|------|
| 見込み | Sonnet 5.5 / effort medium | implementer（Sonnet / medium）+ reviewer（Opus / medium）→ verifier（Sonnet / medium）。文言と CI の条件が変わるので reviewer を付ける。reviewer を先、verifier を後。verifier は、この項目自身の取り込みで、ブランチを push して CI が走るか・ff-only で取り込めるかを確かめる |
| 実施 | Sonnet 5.5 / effort 未確認 | implementer（Sonnet 5.5）+ reviewer（Opus 5.5）→ verifier（モデル未確認） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main + 担当 | Opus 5.5 | 未確認 | 24 | 9,548 | 59,799 | 495,019 | 59% |
| main + 担当 | Sonnet 5.5 | 未確認 | 24 | 5,729 | 32,152 | 349,228 | 41% |
| 合計 |  |  | 48 | 15,277 | 91,951 | 844,247 | 計 951,523 |

- `token-usage.py` は担当ごとに分けられず、モデル別の 2 行で出た（担当のログが一部しか拾えないため、実際より少ない可能性が高い）
- 範囲の終点は、この項目の最後の作業のコミット（差分が paths の外のときの書き足し）

## きっかけ

worktree で編集したあと main に取り込むたびに PR を作るのをやめたい（2026-10-20 ユーザーの依頼）。
参考は meltype-fcitx5-dev の CLAUDE.md の「担当（teammate）」の節（worktree のブランチを `git merge --ff-only` で取り込み、PR は作らない）。

## やったこと

- `.github/workflows/test.yml`・`ruff.yml`・`accuracy.yml`: push の起動条件に `claude/**` を足した。`'!claude/collected-import-**'` で `import_collected.py` のブランチは除く（PR で走るため）。`test`・`ruff` の push にも pull_request と同じ paths を付けた（文書だけの変更では走らない。main への push も同じ絞り込みになる）
- CLAUDE.md の「共同開発」: 「変更は PR なしで main に取り込む」の手順（ブランチを push → `gh run list` で run の ID を調べて `gh run watch <ID> --exit-status` → rebase は `--force-with-lease` → トップで `git merge --ff-only` と `git push origin main` → 片付け）を書いた。push が拒否されたときの戻し方（`git reset --hard origin/main` と `systemctl --user restart bganalyzer`）、run が空のときの扱い、差分が paths の外のときは直前の run の結果でよいことも書いた。取り込んだあと origin の `claude/*` ブランチも消す
- docs/HANDOVER.md（共同開発の相手も同じやり方になること）、docs/raspi.md、recognizer/README.md、`.claude/hooks/no-local-pytest.py` の文言を新しいやり方に直した。`import_collected.py` の自動の PR の記述は今のまま
- 「自動の取り込み」は `import_collected.py` だけを指す語にし、担当の取り込みは「PR なしの取り込み」とした（reviewer の指摘）

## 確かめたこと

- reviewer（`archives/agents/TODO-180/reviewer-report.md`）: 要修正 3 点（`gh run watch` の使い方、`--force-with-lease`、「自動の取り込み」の語の衝突）と検討 5 点を直した。再レビューの 2 点（run が空のときの扱い、reset のあとのサービスの再起動）も直した
- verifier（`archives/agents/TODO-180/verifier-report.md`）: この項目自身の取り込みで手順を実行した。push で `test`・`ruff`・`accuracy` が走り、`gh run watch <ID> --exit-status` で通った。ff-only で main（0f6b248）に入り、origin のブランチを消した。トップの HEAD = origin/main、`/version` も 0f6b248、サービスは active（`- [ ] ローカル:` の確認）
- force push と paths: 木が同じ amend だけだと run は作られず、1 行足すと `test`・`ruff` が走る（実測）。これを CLAUDE.md の手順 2 に書き足した
- main への push で走った `test`・`accuracy`・`ruff` も通った

## 残ること

- 手順の「ff-only にならないとき」「push が拒否されたとき」の分岐は、実際に起きたことがなく、確かめていない

## 分担の振り返り

- reviewer が、手順を書いたとおりに打つと動かない点（引数なしの `gh run watch` は端末でないと待たず、`--exit-status` が無いと落ちても終了コード 0）を、実際に gh を実行して見つけた。implementer は文面を書いただけで気づかなかった。実装と確認を分けた効果が出た
- verifier が、実際に取り込むところまで通して、force push と paths の挙動（run が作られない場合）を実測した。文書だけの項目でも、手順の再現を分ける価値があった
- 見込みと違ったのは、反映の往復が 3 回に割れたこと（implementer への直しの依頼が、reviewer と再レビューの指摘ごとに分かれた）。次に同じ規模なら、手順を書く項目では実装の依頼に「gh や git の手順は実際に打って確かめる」を入れ、最初の実装で run ID・force push の扱いまで書かせる
