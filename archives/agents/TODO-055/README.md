# TODO-055 の分担

- main: 実装（workflow・pyproject・Dockerfile・CI・文書）。差分が小さく、Release の作成に利用者の操作が要ったため implementer は立てなかった
- reviewer（Opus 5.5 / high）: marker の付いた source、uv.lock の互換、wheel の共有ライブラリ、古い記述 → [reviewer-report.md](reviewer-report.md)
- verifier（Haiku 5.5 / medium）: Pi での `uv sync`・pytest、docker build と API、CI → [verifier-report.md](verifier-report.md)

reviewer を先、verifier を後にした（reviewer の指摘で文書と pyproject を直してから確かめるため）。
