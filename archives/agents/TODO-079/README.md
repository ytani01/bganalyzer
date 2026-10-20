# TODO-079 の分担

- 切り分け（teammate）: どの段で崩れるかを先に測る。見立てのまま実装すると、誤った前提で実装・確認・レビューが動くため → `investigate-report.md`
- 実装（teammate、Opus 5.5）: 目から探す道の実装 → `implement-report.md`。利用上限で止まり、別の teammate が引き継いだ → `fix-report.md`（レビューの指摘の直し）、`one-pip-report.md`（1 の目の測定）
- reviewer（Opus 5.5）: 分岐の条件が変わる項目なので、確認とは別に置いた → `review-report.md`、`review2-report.md`
- verifier: 実装と確認を分けるため → `verify-report.md`
- 測る道具: `probe.py`・`count.py`（切り分けと実装）、`probe_pip_calls.py`（目から探す処理が呼ばれた回数）、`one_pip_probe.py`・`one_pip_crop.py`（1 の目の測定）
