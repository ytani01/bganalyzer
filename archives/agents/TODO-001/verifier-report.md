# TODO-001 verifier 報告

対象: `local/todo-001` の作業ツリー差分（`analyzer/analysis.py`、`analyzer/app.py`、`analyzer/test_api.py`）。
手順は `archives/agents/TODO-001/README.md` の「verifier への依頼」に従った。

## 実測: 本物の uvicorn を SIGTERM で止める（port 8001）

各回とも `~/.venvs/bganalyzer/bin/uvicorn app:app --app-dir analyzer --port 8001` を起動し、
`/analyze`（position_id `4HPwATDgc/ABMA`）が 200 を返すのを確かめてから、uvicorn の PID に `kill -TERM` を送った。
止めたあとの 5 秒以内に、対象の PID が消えたかを見た。

| 回 | 修正 | uvicorn PID | 子 PID（resource_tracker / spawn_main） | /analyze | TERM 後 | 結果 |
|----|------|-------------|------------------------------------------|----------|---------|------|
| 1 | あり | 42057 | 42110 / 42111 | 200 | 約 0.21 秒で 3 つとも消えた | 残らず |
| 2 | あり | 42141 | 42191 / 42192 | 200 | 約 0.21 秒で 3 つとも消えた | 残らず |
| 3 | なし（`git stash`） | 42247 | 42297 / 42298 | 200 | 5 秒経っても 2 つ残った | 子が残る |

- 3 回目の後に `pgrep -a -f '[.]venvs/bganalyzer/bin/python'` で残りを確かめ、`kill -9` で片付けた（42297、42298）。
- 3 回目の uvicorn ログは `Shutting down` → `Application shutdown complete.` → `Finished server process` で終わっている。
  つまり lifespan の終了処理は走っているが、子は止まっていない（修正が無いので `shutdown()` が無い）。
- 修正を戻した後、`git stash pop` で 3 ファイルが変更ありに戻ったのを確認した（`M analyzer/analysis.py` など、`git diff --stat` は 33 行追加・6 行削除で、戻す前と同じ）。
- 起動前に `pgrep` で既存の bganalyzer プロセスが無いことを確かめた。片付け後も残りは無い。

## 実測: pytest

- `~/.venvs/bganalyzer/bin/python -m pytest analyzer -q`
  - 出力: `8 passed, 1 warning in 0.46s`（警告は fastapi の httpx 非推奨。修正前からあるので対象外）
  - 終了コード: 0
- 実行後に bganalyzer の残存プロセスは無い。

## 変更ファイルと範囲

`git status --short`:
- `M TODO.md`
- `M analyzer/analysis.py`
- `M analyzer/app.py`
- `M analyzer/test_api.py`
- `?? archives/`（今回の分担の記録。想定どおり）

- `analyzer/` の 3 ファイルは指示どおり（`shutdown()` の追加、lifespan での呼び出し、テストの追加）。差分の形は依頼の記述と一致した。
- `TODO.md` は、チェックボックスを入れたことと、(a) に決めた一文を足したことだけ。依頼範囲から外れるものは無い。
- 他のファイルへの変更は無い。

## 確かめられなかったこと

- **Ctrl-C（SIGINT）での停止は測っていない。** 依頼は SIGTERM のみ。対象の一つなので、必要なら追加で測る必要がある。
- **SIGKILL は対象外**（README の決めごと）。測っていない。
- **`test_server_exit_stops_gnubg_helper` を修正なしで落とす確認は、今回の依頼に含まれていない。** reviewer の担当で、README では main が確かめたとある。verifier としては実測していない。
- uvicorn は 8001 だけで動かした。8000 は使っていない。
- 判断が要る点は無し。SIGTERM の実測は修正前後で結果がはっきり分かれた。
