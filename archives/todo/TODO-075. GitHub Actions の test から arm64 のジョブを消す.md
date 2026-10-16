# TODO-075. GitHub Actions の test から arm64 のジョブを消す

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort low | main（実装）+ verifier（Haiku 5.5 / medium） |
| 実施 | Opus 5.5 / effort low | main（実装）+ verifier（Haiku 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | low | 10 | 2,684 | 36,399 | 327,981 | 91% |
| verifier | Haiku 5.5 | medium | — | — | — | — | 9% |
| 合計 |  |  |  |  |  |  | 計 403,433 |

- verifier は作業のコミットより後に動いたので `token-usage.py` の範囲に入らない。Agent ツールの通知の合計（36,359）だけを書き、内訳は無い
- verifier は定義のまま（`model: haiku`、`effort: medium`）

## きっかけ

arm64 で流していた理由のうち、CPU による読みの違いは TODO-074 でやめた。残る gnubg の aarch64 の wheel の確認は、
依存が変わるときだけ要り、壊れていても Pi の `uv sync --frozen` と再起動で分かるので、毎回の PR では流さない（ユーザーの決定、2026-10-16）。

## やったこと

- `.github/workflows/test.yml`: matrix をやめ、`ubuntu-latest` だけで流す
- `.github/workflows/gnubg-wheel.yml`: ビルドしたコンテナの中で wheel を `pip install` し、`/` から `import gnubg` できたときだけ Release に置く
- `CLAUDE.md` の「共同開発」: 依存（`pyproject.toml`・`uv.lock`）を変えた PR では、Pi で `uv sync --frozen` と再起動が通るかを docs/PI_CHECKS.md に足す
- `README.md`・`docs/HANDOVER.md`: 「x86_64 と arm64 で確かめる」を、x86_64 だけで、arm64 は依存を変えたときに Pi で確かめる、に直した

PR #236。

## 確かめたこと

- PR #236 の `test` は `pytest`（ubuntu-latest）の 1 件だけで、通った。arm のジョブは出ていない
- 「test が arm64 で確かめる」という古い記述は残っていない（recognizer の経緯の記述は対象外）
- `gnubg-wheel.yml` の import の確認は、`sh -ec` の中なので失敗すれば止まる（読んだだけ）

## 残ること

- `gnubg-wheel.yml` はタグを打たないと走らないので、import の確認が実際に動くかは次に wheel を作り直すときに分かる

## 分担の振り返り

- verifier は CI のジョブの数と結果、古い記述が無いことを確かめた。食い違いは見つけなかった
- 見込みどおり。verifier の大半は CI を待つ時間で、トークンは少なかった
- 次に同じ規模（CI の設定と文書の数行）なら同じ組み方でよい。古い記述の点検は main が `rg` で済ませているので、verifier には CI の結果だけを頼めばさらに減らせる
