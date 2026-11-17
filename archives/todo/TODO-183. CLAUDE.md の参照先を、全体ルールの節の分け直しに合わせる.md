# TODO-183. CLAUDE.md の参照先を、全体ルールの節の分け直しに合わせる

| | main | 担当 |
|---|---|---|
| 見込み | Opus 5.5 / effort medium | main（数行の変更）+ reviewer（Sonnet 5.5 / low）+ verifier（Haiku 5.5 / low） |
| 実施 | Opus 5.5 / effort low | main（数行の変更）+ wording（Sonnet 5.5 / low）+ reviewer（Sonnet 5.5 / low）+ verifier（Haiku 5.5 / low） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | low | 59 | 9,365 | 31,059 | 2,588,813 | 88% |
| verifier | Haiku 5.5 | low | 10 | 2,441 | 30,589 | 110,901 | 5% |
| reviewer | Sonnet 5.5 | low | 8 | 879 | 30,059 | 83,376 | 4% |
| wording | Sonnet 5.5 | low | 6 | 1,317 | 27,443 | 60,192 | 3% |
| 合計 |  |  | 83 | 14,002 | 119,150 | 2,843,282 | 計 2,976,517 |

- 項目を立てたコミットが main に入る前に集計したので、`--since` に、項目を立てる 3 分前（2026-11-17 14:05:36）を渡した
- wording は、項目を立てたときの言葉の確認（全体ルールの TODO-116）。見込みの行には書いていなかった

## きっかけ

起動時に「全体ルールが変わった」という知らせが届いた（`.claude/global-rules-seen` は 103、全体ルールは 152 番目の変更まで進んでいた）。

## やったこと

- 全体ルールの 104〜152 番目の変更を見て、このプロジェクトの `CLAUDE.md` と食い違う点を探した。
  食い違っていたのは、`CLAUDE.md` の「共同開発」が、今は無い全体の節「担当（teammate）」を指していることだけだった
- `CLAUDE.md` の参照先を「担当の動かし方」に直した
- `.claude/global-rules-seen` を 152 にした（リポジトリには入っていない）

## 確かめたこと

- reviewer: 参照先の節が実在し、worktree を使わない既定が書いてあること。今は無い節を指す箇所がほかに無いこと
- verifier: 108 行目の文言、節の存在、seen と今の番号がどちらも 152、変わったのが CLAUDE.md と TODO.md だけ

## 分担の振り返り

- wording は見出しの「103〜152 番目」が伝わらないと指摘し、直した。reviewer と verifier は問題を見つけなかった
- 見込みとの違いは、wording を見込みの行に書き忘れたことだけ
- 次に同じ規模なら、reviewer と verifier を 1 回ずつにした今回の組み方でよい。main の割合が 88% なので、全体ルールの変更を読む作業を短くすることが、減らせる余地になる
