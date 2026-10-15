# TODO-064 確認報告（PR #211、head eed5625）

確認対象の head は `eed56251c112b55217986b10f832593a5cad4f52`。`gh pr view` の headRefOid と、確認した 2 つの run の headSha が一致した。

## 1. `gh pr checks 211 --watch --interval 60`（終了コード 0）

| チェック名 | 結果 | 時間 |
|---|---|---|
| pytest (ubuntu-latest) | pass | 1m26s |
| pytest (ubuntu-24.04-arm) | pass | 1m44s |
| accuracy | pass | 2m35s |

- `test` ワークフローの job 名は `pytest`（matrix で 2 本）。ワークフロー名は `test`。2 本とも走って通った。
- `cpu-match` のチェックは出なかった。

## 2. cpu-match と accuracy

- `cpu-match`: 走っていない。正しい。
- `accuracy`: **走った（pass）。** 依頼文の「走らないのが正しい」とは違う。
  - 原因（出力と設定から読んだ内容）: PR の変更ファイルに `recognizer/README.md` が含まれる。
    `accuracy.yml` の `pull_request.paths` は `recognizer/**` を含むので、`.md` でもトリガーされる。
  - `accuracy.yml` の `paths` は変更していない（diff に含まれない）。
  - 「recognizer/ を変えていない」は誤り。変えたのは README だけで、`recognizer/` 配下の文書は accuracy のトリガー対象になっている。
  - 判断が要る点: `accuracy` の paths に `**.md` 除外を入れるかどうか。TODO-064 の範囲（`test.yml` の paths-ignore）の外。報告のみ。

## 3. `.github/workflows` の中身（ref=claude/ci-waste）

- `accuracy.yml`
- `gnubg-wheel.yml`
- `test.yml`
- `cpu-match.yml` は無い。正しい。

## 4. test.yml の paths-ignore

- `pull_request:` に `paths-ignore: ['**.md', 'docs/**', 'archives/**']` がある。正しい。
- `push:` は `branches: [main]` のみで、paths-ignore は無い。正しい。
- 取得元: `git show origin/claude/ci-waste:.github/workflows/test.yml`（内容を全文確認）。

## 確かめられなかったこと・判断が要ること

- 文書だけの PR で `test` が走らないことは、この PR（コード変更あり）では確かめていない。`paths-ignore` の設定を読んだだけで、文書だけの PR での挙動は未実測。
- 上記 2 の accuracy の扱い（`recognizer/**` に `.md` を含めるかどうか）は管理者の判断が要る。
- コードは変更していない。
