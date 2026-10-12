# TODO-001 の分担

| 担当 | やること | 理由 |
|------|----------|------|
| main | 原因の確認と実装、テストの追加 | 変更は 3 ファイル・十数行で、分けるほどではない |
| reviewer | 差分のレビュー | 終了時の処理という分岐が変わるので、確認とは別に「良いか」を見る |
| verifier | 本物の uvicorn を SIGTERM で止めて子プロセスが残らないかを実測 | 実装した本人の「動くはず」で済ませない |

reviewer を先に、verifier を後に回す。

## 前提（両担当共通）

- 対象の差分: `git diff main -- analyzer/`（ブランチ `local/todo-001`）
- 決めたこと: 面倒を見るのは **SIGTERM・Ctrl-C で正常に止めたときだけ**。
  親が SIGKILL で死んだときに子が残るのは対象外（指摘しなくてよい）
- 原因: uvicorn（0.54）の `Server.capture_signals` は、正常に止めたあとで
  受けたシグナルを `signal.raise_signal` で投げ直す
  （`~/.venvs/bganalyzer/lib/python3.13/site-packages/uvicorn/server.py:345`）。
  そのため atexit が走らず、`ProcessPoolExecutor` が閉じられない
- Python は `~/.venvs/bganalyzer`（3.13）を使う。システムの 3.14 には gnubg が入らない
- コードは直さない。見つけたことは報告だけ。境界線上の判断もしない
  （「実害は未確認」と添えて報告する）

## reviewer への依頼

差分を読み、次を見る。

- lifespan の終了処理で `shutdown()` を呼ぶ形で、正常終了時に子が確実に止まるか
- `shutdown()` と `_call_engine` の間で、`_pool` の扱いに食い違いが無いか
  （解析の途中で止めたとき、shutdown のあとに呼ばれたとき、など）
- 追加したテスト `test_server_exit_stops_gnubg_helper` が、修正を外すと落ちる
  形になっているか（main が 1 回試し、外すと落ちた）
- `app.py` のコメントの主張が uvicorn のソースと合っているか

見なくてよいもの: SIGKILL 時の扱い、既存のテストの書き方、httpx の非推奨の警告
（修正前からある）。

報告: `archives/agents/TODO-001/reviewer-report.md`。問題が無い観点は 1 行、
問題だけ詳しく。返事は「終わったか・報告ファイルのパス・判断が要る点」だけ。

## verifier への依頼

本物のサーバーで、止めたあとに子プロセスが残らないことを測る。

1. `cd /home/ytani/work/bganalyzer` で
   `~/.venvs/bganalyzer/bin/uvicorn app:app --app-dir analyzer --port 8001` を
   バックグラウンドで起動する（8000 は使わない）
2. `curl --max-time 30 localhost:8001/analyze -H 'content-type: application/json' -d '{"position_id":"4HPwATDgc/ABMA"}'`
   で 200 が返ることを確かめる（子プロセスが立ち上がる）
3. `pgrep -a -f '.venvs/bganalyzer/bin/python'` で uvicorn と子 2 つ
   （`spawn_main` と `resource_tracker`）の PID を記録する
4. uvicorn の PID に `kill -TERM` を送り、5 秒以内に 3 つとも消えるかを見る。
   **`pkill` は使わない**（自分のシェルを巻き込む）。残ったら PID を指定して kill して片付ける
5. 1〜4 を 2 回行う。比較のため、`git stash` で修正を外した状態でも 1 回行い、
   子が残ることを確かめる（終わったら `git stash pop` で戻し、`git status` で
   3 ファイルが変更ありに戻ったことを確かめる）
6. `~/.venvs/bganalyzer/bin/python -m pytest analyzer -q` が通ることを確かめる

報告: `archives/agents/TODO-001/verifier-report.md`。各回の PID と、
消えたか・残ったかを載せる。返事は「終わったか・報告ファイルのパス・判断が要る点」だけ。
