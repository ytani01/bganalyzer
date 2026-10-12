# TODO-001 reviewer の報告

対象: `git diff main -- analyzer/`（`analysis.py`・`app.py`・`test_api.py`）。

## 要修正

なし。

## 検討

なし。

## 好みの範囲

なし。

## 観点ごとの結果

- **lifespan で `shutdown()` を呼ぶ形で、正常終了時に子が止まるか:** 問題なし。
  uvicorn 0.54 の `Server.shutdown()` は、接続とタスクが片付くのを待ってから
  `force_exit` でなければ `lifespan.shutdown()` を呼ぶ（`server.py` 310 行付近）。
  シグナルの投げ直しはそのあと、`capture_signals` の `finally` の後ろ
  （345 行）。`_pool.shutdown()` は既定の `wait=True` で子を join するので、
  投げ直しの前に子は終わっている。Ctrl-C を 2 回押した `force_exit` では
  lifespan の終了処理が飛ばされるが、正常な終了ではないので対象外
  （その場合も SIGINT の投げ直しは `KeyboardInterrupt` になり atexit が走るはず。
  未確認）
- **`shutdown()` と `_call_engine` の `_pool` の扱い:** 食い違いなし。
  - 解析の途中で止めたとき: uvicorn は接続が閉じるまで lifespan の終了処理に
    進まないので、走っている解析と `shutdown()` は重ならない（コードを読んで確認。
    `timeout_graceful_shutdown` を設定したときは重なりうるが、このプロジェクトでは
    設定していない）
  - shutdown のあとに呼ばれたとき: `_pool` を `None` に戻すので、次の
    `_call_engine` が新しく作る。2 回続けて呼んでも何もしない。
    `~/.venvs/bganalyzer` で `analyze → shutdown → shutdown → analyze` を実行し、
    `_pool` が `None` になったあと別の pool が作られることを確かめた
  - 複数スレッドから `_pool` を守る仕組みが無いのは修正前からで、この差分では
    増えていない
- **`test_server_exit_stops_gnubg_helper` は修正を外すと落ちるか:** 落ちる。
  リポジトリを scratchpad に写し、3 通りで `-k test_server_exit` を実行した。

  | 状態 | 結果 |
  |------|------|
  | 修正のまま | 1 passed |
  | `FastAPI(..., lifespan=lifespan)` の引数を外す | 1 failed（`_pool is None` で落ちる） |
  | `shutdown()` の `_pool.shutdown()` を `pass` にする | 1 failed（子が生きたまま） |

  リポジトリでの全体の実行も `8 passed`。
- **`app.py` のコメントの主張:** uvicorn のソースと合っている。
  `capture_signals` は元のハンドラ（SIGTERM では `SIG_DFL`）に戻してから
  `signal.raise_signal` するので、プロセスは SIGTERM で終わり atexit は走らない。
  「after this」も、投げ直しが lifespan の終了処理より後なので正しい。
  `shutdown()` の docstring も「なぜ呼ぶか」を書いている
- **範囲:** `analyzer/` の差分は依頼の 3 ファイルだけ。指示に無い変更は無い
- **書式:** 既存のファイルと揃っている（`test_api.py` の 1 行が 101 字だが
  修正前からある行）

## 作り込みすぎ

作り込みすぎ: なし（`shutdown()` は pool を持つ `analysis.py` に置くのが最小で、
lifespan も 2 行。Lean already. Ship.）
