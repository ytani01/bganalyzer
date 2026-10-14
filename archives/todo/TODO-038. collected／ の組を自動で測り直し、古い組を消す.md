# TODO-038. collected/ の組を自動で測り直し、古い組を消す

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort high | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Sonnet 5.5 / medium） |
| 実施 | Opus 5.5 / effort low | main（実装）+ reviewer（Opus 5.5 / high、2 回）+ verifier（Sonnet 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | low | 118 | 59,214 | 91,696 | 10,836,674 | 80% |
| reviewer | Opus 5.5 | high | 72 | 10,301 | 203,265 | 2,538,487 | 20% |
| 合計 |  |  | 190 | 69,515 | 294,961 | 13,375,161 | 計 13,739,827 |

- verifier は定義のモデルが haiku。Pi でイメージを作り直し、別のコンテナを立てて /samples に送る実測があるので Sonnet 5.5 に上書きした
- verifier は終点のコミット（ae90907）のあとに動いたので、上の表に入っていない（完了の通知では 32,463 トークン）
- 範囲は立てたとき（2026-10-14）から。`claude -p` を含める相談と、途中でやめた作りの分も入っている

## きっかけ

ai1 の依頼（2026-10-14）: 「Pi に残す」で集まった組が、ある程度たまったら自動で測り直し、要らなくなったデータは消す。

## 決めたこと

- **いつ:** 前に測ったときから新しい組が 10 以上増えたら。きっかけは、サーバーが組を保存したとき（ai1「cron は不要なはず」）
- **消す組:** 読み違いの無い組は新しい 50 組だけ残し、古いものから消す。読み違いのある組は直す材料なので消さない
- **結果:** `collected/report.md`。認識を直すのは、ai1 が Pi の Claude Code に頼んだとき

## やったこと

- `recognizer/collected.py`（recognizer 0.8.0）: 全部の組を `evaluate.run` で測り、`report.md` と `.measured.json` を書き、読み違いの無い古い組を消す。
  `/samples` は公開で誰でも送れるので、正解の欄の形を `valid()` で確かめ、形の違う組は測らず、`report.md` には正解の中の文字を出さない
- `analyzer/app.py`（analyzer 0.26.0）: `save_sample` のあと、新しい組が 10 以上で前の測り直しが動いていなければ、`nice -n 19` の子プロセスで起動する。
  失敗の理由は `collected/measure.log`。起動に失敗しても保存は 200
- テスト（`analyzer/test_collected.py`、`test_api.py` の `test_samples_measured_again_after_ten_new`）、docs/raspi.md、analyzer/README.md、recognizer/README.md、PI-019

## 途中でやめた作り

1. 測り直したら cron から `claude -p` を起動して直させ、PR を作る。そのあとマージと Pi の更新まで自動にする（ai1 が選んだ）
2. reviewer が、`/samples` に仕込まれた文に従った `claude -p` が、編集した `recognizer/*.py` を `evaluate.py` 経由で Pi の上で動かせる
   （ytani は docker グループで push とマージの権限もある）こと、`Read(**/*.truth.json)` の禁止が `--add-dir` の先に効かないこと、
   `Bash(prefix:*)` の書き方では push もできないことを実測で示した
3. `claude -p` を `--restricted` で worktree に閉じ込め、測るのはネットワークの無いコンテナ、関門と PR とマージはスクリプト、の形に作り直す途中で、
   Claude Code の auto mode が「人のレビューなしにマージと本番の更新をするエージェントを作る（Create Unsafe Agents）」として止めた
4. ai1 が cron をやめると決め、今の形にした。自動のマージも `claude -p` の起動もしない

## 確かめたこと

- verifier（[verifier-report.md](../agents/TODO-038/verifier-report.md)）: pytest は 1 failed（イメージに git が無い既知の 1 件）・43 passed。
  `valid()` を常に True にすると `test_a_truth_sent_by_anyone_is_not_used_and_not_shown` が、`poll()` の条件を外すと
  `test_samples_measured_again_after_ten_new` が落ちた。別のコンテナに /samples で 10 組送ると report.md と measure.log ができ、
  20 組で 2 回目が起動し、`ni=19` で動いた
- reviewer の 2 回目（[reviewer-report-2.md](../agents/TODO-038/reviewer-report-2.md)）: 要修正なし。検討のうち、evaluate.py で collected/ を測る手順、
  `valid()` のテスト、失敗の記録、優先度、Popen の失敗で 500、analyzer/README.md を直した

## 残ること

- 公開の POST で 10 組ずつ送れば、何度でも測り直しを起こせる（最大 1000 組）。優先度は下げたが、/analyze が遅くなるかは測っていない
- 手で `--force` を走らせたのと自動の測り直しが同時に動くと、片方が消した組をもう片方が読んで「読めなかった」になることがある
- 実際に 10 組たまったときの動きは PI-019 で ai1 が使ってから見る

## 分担の振り返り

- reviewer（1 回目）は、`claude -p` に任せる作りの危うさを実測で示した（権限ルールの解釈、`--add-dir` の先の Read、正解の文字列が report に出ること、公開の POST 1 回で毎日止まること）。
  これが無ければ、任意のコードを動かせるうえ push もできない作りをそのまま入れていた。2 回目は `valid()` がテストで守られていないことと、子プロセスの失敗が残らないことを見つけた。
  verifier は、壊すと落ちること、サーバー経由で 2 回起動して nice で動くことを実測した
- 見込みとの差: 作りを 2 回変えたので main と reviewer が見込みより大きくなった。main の effort は low で足りた
- 次に同じ規模なら: 公開の入口から来るデータを自動の処理に渡す項目では、権限と信頼の範囲を設計の段階で reviewer に見せてから実装する。
  エージェントにマージや本番の更新をさせる案は、auto mode に止められることも含めて、最初に利用者に示す
