# TODO-168. ruff で lint と format を通す

|      | main | 担当 |
|------|------|------|
| 見込み | Sonnet 5.5 / effort medium | implementer（Sonnet 5.5）+ verifier（Sonnet 5.5 / medium）。lint の指摘の直しで分岐や条件が変わる箇所があれば reviewer（Opus 5.5 / high）を足す |
| 実施 | Opus 5.5 | implementer（Sonnet 5.5）+ reviewer（Opus 5.5）+ verifier（Sonnet 5.5） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main（implementer・reviewer・verifier を含む） | Opus 5.5 / Sonnet 5.5 | 記載なし | 260 | 60,600 | 157,262 | 14,180,720 | 99% |
| claude-code-guide | Haiku 5.5 | 記載なし | 8 | 390 | 67,963 | 128,504 | 1% |
| 合計 |  |  | 268 | 60,990 | 225,225 | 14,309,224 | 計 14,595,707 |

- `token-usage.py` は implementer・reviewer・verifier を main と分けて出せなかった（担当の記録が `subagents/` に無い）。モデル別の内訳は Opus 5.5 が 66%、Sonnet 5.5 が 33%
- 始点は `--since '2026-10-20 03:10:00'`（TODO-167・TODO-166 のマージのあと、着手の時刻）。終点は決着の前の最後のコミット（HANDOVER の直し）

## きっかけ

Python のコードにリンターが入っておらず、`pyproject.toml` にも GitHub Actions にも設定が無かった。

## やったこと

- ruff を dev 依存に入れ、`pyproject.toml` に設定を足した。規則は `select = ["E", "F", "I"]`・`ignore = ["E501"]`、行の長さは既定の 88、`archives/` は `extend-exclude`、自作のモジュールの見分けに `src = [".", "recognizer", "analyzer", "tools"]`
- `ruff format` で 46 ファイルを整形した（整形だけのコミット）
- safe な自動修正（I001・E401・F401）と、手で直した指摘（E731 の 11 件を `def` に、E741 の 7 件を改名）を別のコミットにした。noqa は足していない
- `.github/workflows/ruff.yml`（`uv run ruff check` と `uv run ruff format --check`）を足した
- `CLAUDE.md` のコマンドとマージの条件、`docs/HANDOVER.md` の CI の節と自動マージの条件に `ruff` を足した
- 挙動は変えていないので、analyzer・recognizer の版は上げていない

## 確かめたこと

- `uv run ruff check` と `uv run ruff format --check` が通る
- 整形と自動修正のコミットは、前のコミットの木に同じコマンドをかけた結果と `diff -r` で一致した（reviewer）
- 違反（未使用 import、整形の乱れ）を入れると、`ruff check` と `ruff format --check` がそれぞれ終了コード 1 で落ちる（verifier。スクラッチで確認）
- PR #502 の CI（`pytest`・`accuracy`・`ruff`）が通った

## 分担の振り返り

- **見つけたこと:** reviewer が `known-first-party` を足す代わりに `src` を 1 行足すと、自作のモジュールが third-party と分かれて並ぶと指摘した。マージの条件と CI の節に `ruff` が無いことと、HANDOVER の自動マージの条件が CLAUDE.md と食い違うことも reviewer が見つけた
- **見込みと食い違った理由:** 見込みでは reviewer は「分岐や条件が変わる箇所があれば」だった。規則が E・F・I に決まり、直しは `lambda`→`def` と改名だけで挙動が変わる箇所は無かったが、設定とマージの条件の見落としを拾うために reviewer を入れて効いた。実装は途中で規則が既定の規則から E・F・I に変わり、コミットを作り直した（規則は件数を測ってから決める流れで、方針の訂正が 1 回入った）
- **次に同じ規模ならどう組むか:** 設定を入れる項目は、規則の選び方（既定か、世の中でよく使われているものか）を先に利用者へ確かめてから実装に渡す。そうすれば作り直しが要らない。マージの条件や CI の節のような文書の追従も、実装の依頼にはじめから書いておく
