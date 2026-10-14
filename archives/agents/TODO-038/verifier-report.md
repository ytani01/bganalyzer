# verifier 報告（TODO-038、HEAD ae90907）

## 1. テスト
`docker compose up -d --build` 後のイメージで実行。終了コードは取っていない（pipe 経由）。
- 要約行: `1 failed, 43 passed, 6 skipped, 1 warning in 57.20s`
- 落ちたのは `FAILED analyzer/test_api.py::test_version_reports_both_parts_and_commit` のみ（想定どおり）。
- 6 skipped の理由は見ていない（`-rs` 未確認）。

## 2. 壊すと落ちる
- `valid()` を常に True（docstring の直後に `return True`）: `FAILED analyzer/test_collected.py::test_a_truth_sent_by_anyone_is_not_used_and_not_shown` / `1 failed, 2 passed`
- `measure_collected` の `(_measuring and _measuring.poll() is None) or` を除去: `FAILED analyzer/test_api.py::test_samples_measured_again_after_ten_new` / `1 failed, 4 passed, 30 deselected`
- 両方 `git checkout` で戻し、`git status --short` は空。

## 3. 本物で動く
- /version: `{"analyzer":"0.26.0","recognizer":"0.8.0","commit":"ae90907","samples":true}`
- 手動 collected.py（作業用ディレクトリ、user-v0〜v9）: 出力 `measured`。`report.md` と `.measured.json` ができた。先頭: `組: 10（新しい組 10）。読み違いのある組 0、正解の形が違う組 0` / `読み違いの無い古い組を 0 消した`
- サーバー経由（`bgv`、:8001、BG_SAMPLES_DIR=/d）: 10 組送信で全て `{"saved":"user-vN"}`。数十秒以内に `report.md`（`組: 10（新しい組 10）…`）と `measure.log`（空 = エラー無し）ができた。
- さらに 10 組（w0〜w9）を送ると 2 回目が起動し、report.md は `組: 20（新しい組 10）` に更新された。
- nice: コンテナに `ps` が無く `docker exec bgv ps` は `executable file not found`。代わりに /proc/<pid>/stat で、実行中の `/app/.venv/bin/python /app/recognizer/collected.py /d` が `ni=19` を確認。終了も確認（プロセスが消えた）。
- 1 回目の測り直しは 10 組送信後すぐ終わっており（約 1 秒）、nice は 2 回目でしか見ていない。
- 本物の `collected/` は変更なし（2 ファイルのまま）。`docker stop bgv` 済み。

## 判断が要る点
なし。指示の `docker exec bgv ps` が使えない点（イメージに ps が無い）だけ報告。
