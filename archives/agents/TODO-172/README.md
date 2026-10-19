# TODO-172 の分担

- implementer（Opus 5.5 / high）: 時間の測定、`recognizer/corners.py` の書き換え、前後の一致の確認 → [implementer-report.md](implementer-report.md)
- reviewer（Opus 5.5 / high）: 差分のレビュー。コードが変わるので入れ、verifier より先に回した → [reviewer-report.md](reviewer-report.md)
- verifier（Sonnet 5.5 / medium）: 全サンプルでの一致と速さの測り直し → [verifier-report.md](verifier-report.md)

実装と確認を分けたのは `~/.claude/CLAUDE.md` の決まりどおり。込み入った書き換えなので implementer は Opus にした。
測る道具（`record_corners.py`、`ab_time.py`）と前後の記録（`corners-before.json`、`corners-after.json`）もここにある。
