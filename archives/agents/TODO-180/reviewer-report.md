# TODO-180 reviewer の報告

対象: `git diff origin/main...claude/todo-180-ff-merge`（111b71c まで）

## 要修正

### 1. `CLAUDE.md:127` — `gh run watch` は引数なしでは担当から使えない

- 問題: 手順 2 が「`gh run watch` で結果を待つ」だけで、run ID の取り方が無い。
- 根拠（実測、gh 2.102.0）: 端末でない標準入力で `gh run watch` を引数なしで実行すると
  `run ID required when not running interactively` を出して終わる（終了コード 0 ではあるが、待たない）。
  Bash ツールは端末ではないので、書いてあるとおりに打つと待たずに先へ進む。
- さらに、push 1 回で `test`・`ruff`・`accuracy` が別々の run になるので、1 つ watch しても残りは待てない。
  `gh run list --branch claude/<作業内容> --commit <SHA>` などで run を列挙し、それぞれ `gh run watch <id> --exit-status` する、のように
  ID の取り方と `--exit-status`（付けないと落ちても終了コード 0）まで書かないと「落ちたものは main に入れない」を担保できない。
  フックの文言（`.claude/hooks/no-local-pytest.py:26`「push したあと gh run watch」）も同じ。

### 2. `CLAUDE.md:128` — rebase のあとの push に force が要ることが書いていない

- 問題: 手順 3「`git rebase origin/main` して push し直し」。rebase で履歴が変わるので、普通の `git push` は non-fast-forward で拒否される。
- 根拠: git の挙動（rebase 済みのブランチを既存の origin ブランチへ push すると拒否）。`--force-with-lease` を書く必要がある。
  `docs/HANDOVER.md:59-60`（「取り込む直前に最新 main へ rebase し」）も同じく push の仕方が無い。
- 実害は未確認（verifier の取り込みで main が進んでいなければ通ってしまうので、この項目の確認では出ない可能性が高い）。

### 3. `docs/HANDOVER.md:33,59` と `:111-112` — 「自動の取り込み」が 2 つの別のものを指している

- 問題: `:33`「自動の取り込み（ブランチを push して CI を通し…ff-only で main に取り込み）」、`:59`「自動の取り込み（2026-10-20 から PR は作らない…）」は
  担当が自分で ff-only で入れることを指す。一方 `:111-112`「PR（自動の取り込みが作る）」「自動の取り込みのブランチ `claude/collected-import-*`」、
  ワークフローのコメント（`test.yml`・`ruff.yml`・`accuracy.yml` の「自動の取り込み（recognizer/import_collected.py）」）、
  `CLAUDE.md:132` は `import_collected.py` の PR を指す。同じ文書の中で同じ語が別のものを指し、`:59` の「PR は作らない」と `:111` の「PR（自動の取り込みが作る）」が矛盾して読める。
- 根拠: 読んだ文書。元の語は「自動マージ」で、置き換えで衝突した。担当のほうは「取り込み」「担当が自分で取り込む」など、別の語にする必要がある。

## 検討

### 4. `CLAUDE.md:128` — rebase して force push したあと、paths の絞り込みで CI が走らないことがある（未確認）

- 問題: 既存ブランチへの push では、paths はその push の前後の差（古い head と新しい head）で判定される（GitHub Actions の仕様。記憶による、未確認）。
  rebase 前後の差は「その間に main に入った変更」になるので、間に入ったのが文書だけなら、ブランチが .py を変えていても `test`・`ruff` が走らない。
  手順 3 の「CI をやり直す」が起きず、`gh run watch` で待つ run が無い（または rebase 前の run を見てしまう）。
- 根拠: 未確認。verifier に、rebase して force push したときに run が作られるかを見てもらうのが確実。実害は未確認。
  rebase 前の run が通っていればよいとするか、`workflow_dispatch`（`test`・`ruff` には無い）で流し直すかは判断が要る。

### 5. `CLAUDE.md:129` — `git push origin main` が拒否されたときの戻し方が無い

- 問題: 手順 4 は「ff-only にならなければ 3. に戻る」だけ。手順 3 の fetch のあと別の担当が main を push すると、
  トップの `git merge --ff-only` は通り（トップの main はまだ古い）、`git push origin main` が拒否される。
  このときトップの main だけが進んだまま残り、post-merge でサービスも再起動される。トップを `origin/main` に戻す手順が要る。
- 根拠: 読んだ手順と git の挙動。並べて作業する前提（CLAUDE.md「同じマシンで並べて作業する」）なので起こりうる。実害は未確認。

### 6. `TODO.md:77,82` — 追加で決まったことが TODO.md に反映されていない

- `:77` のチェック項目は「今の paths の絞り込みは保つ」のままだが、push にも paths を付けて main への push の挙動を変えた（文書だけの main への push で `test` が走らなくなった）。
- `:82` の「何を決めるか: CI の待ち方…」は決まった（書く）のに残っている。
- push の paths と `claude/collected-import-*` の除外も「決まったこと」に無い。決着時に archives へ移す前に直すのでもよい。

## 問題なしの観点

- ワークフローの起動条件: 否定パターンは肯定パターンの後ろにあり有効。`branches` と `paths` は両方満たすときに走る。`claude/collected-import-` + 日時（`import_collected.py:39`）は除外に合う。accuracy の push・PR の paths は保たれている。main への push で走らなくなるのは文書だけの変更の `test`・`ruff` だけ（決まったとおり）。他のワークフローは `gnubg-wheel.yml`（タグのみ）で影響なし。
- PR を前提にした記述の直し漏れ: 残りは自動の取り込み PR（`CLAUDE.md:51`、`recognizer/README.md:788`、`docs/raspi.md:207-218`）と過去の経緯（`docs/HANDOVER.md:26,117`）だけで、正しい。
- CLAUDE.md・HANDOVER・raspi・recognizer/README の CI の条件の説明は互いに一致（上の 3. の語の衝突を除く）。
- 造語: 上の 3. 以外は無し。「変更を取り込む」「その組を消す変更を取り込む」は自然。
- 範囲: 指示に無い変更なし。
- 作り込みすぎ: なし
