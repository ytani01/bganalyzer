# TODO-055. Pi（aarch64）でも `uv sync` / `uv run` をクラウドと同じに通す

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort medium | implementer（Sonnet 5.5 / medium）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |
| 実施 | Opus 5.5 / effort medium | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | medium | 76 | 17,940 | 43,948 | 3,168,967 | 81% |
| reviewer | Opus 5.5 | high | 28 | 135 | 49,448 | 486,865 | 13% |
| verifier | Haiku 5.5 | medium | 16 | 59 | 33,140 | 188,483 | 6% |
| 合計 |  |  | 120 | 18,134 | 126,536 | 3,844,315 | 計 3,989,105 |

- 実装は小さく（設定 1 行と workflow 1 本、Dockerfile の削除）、Release を作る操作に利用者の手が要ったので、implementer を立てずに main がした
- 集計は 2 回に分けて足した（実装のコミットのあと reviewer・verifier が動いたため。2 回目は `--since '2026-10-15 19:03:24'`）。main には TODO-056 を立てた分も入っている

## きっかけ

PyPI の gnubg には aarch64 の Linux の wheel が無く、Pi では `uv sync` が落ちた。手でビルドして `uv run --no-sync` で回避していた。
利用者の希望（2026-10-15）: クラウドと Pi の環境を同じにし、同じコマンドで動かしたい。

## やったこと

- `.github/workflows/gnubg-wheel.yml`: タグ `gnubg-*` の push で、arm64 のマシン上の `python:3.12-slim-bookworm` で gnubg-pypi（Dockerfile と同じコミット）から wheel をビルドし、Release に置く。
  `gnubg-1.1.0a16` で実行した（タグの push は auto mode に止められたので利用者がした）
- `pyproject.toml`: `[tool.uv.sources]` で aarch64 のときだけ Release の wheel を使う。x86_64 などは PyPI のまま。版を `==1.1.0a16` に揃えた（reviewer の指摘）。`uv.lock` を作り直した
- Dockerfile: arm64 のソースからのビルドを消し、`uv sync --frozen --no-dev` だけにした
- CI: `test` に `ubuntu-24.04-arm` を足した。`cpu-match` の `--no-install-package gnubg` と `--no-sync` を消した
- README・analyzer/README.md・docs/raspi.md・docs/HANDOVER.md の、ソースからのビルドや「arm64 では uv sync が失敗する」の記述を直した
- docs/PI_CHECKS.md に PI-038（マージ後に Pi で `docker compose up -d --build` と `uv run pytest`）を足した

## 確かめたこと

verifier（[archives/agents/TODO-055/verifier-report.md](../agents/TODO-055/verifier-report.md)）:
Pi で `uv sync --frozen` が通り、入った gnubg は Release の URL のもの。`uv run pytest analyzer`（`--no-sync` なし）は 74 passed。
`docker build` でソースからのビルドが走らず、起動したコンテナで `/analyze` と `/analyze-photo` が gnubg の評価を返した。
PR #176 の CI（test・cpu-match・docker の x86_64 と arm64、accuracy）はすべて通った。

## 残ること

- PI-038（マージ後の本番の Pi）
- Docker そのものをやめる件は TODO-056

## 分担の振り返り

- reviewer: 依頼の `rg` に掛からない古い記述 2 か所（README・docs/HANDOVER.md）と、x86_64 だけ版が上がりうる点を見つけた。uv 0.11 で revision 5 の `uv.lock` が読めることも実際に確かめた
- verifier: 食い違いは無し。pytest の終了コードを取り損ねたが、件数で足りた
- 見込みとの差: implementer を立てなかった。Release の作成に利用者の操作が挟まり、実装は数ファイルの小さな差分だったため
- 次に同じ規模なら: 実装は main、reviewer と verifier だけ立てる。reviewer への依頼の `rg` は、古い前提の言い回し（「失敗」「Docker で動かす」など）まで広げる
