# TODO-001. サーバーを止めると gnubg の子プロセスが残る

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort medium | main（実装）+ reviewer（Opus / high）+ verifier（Haiku / medium） |
| 実施 | Opus 5.5 / effort 不明 | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | 不明 | 54 | 8,183 | 18,325 | 1,955,317 | 80% |
| reviewer | Opus 5.5 | high | 16 | 2,071 | 35,226 | 195,507 | 9% |
| verifier | Haiku 5.5 | medium | 20 | 2,071 | 32,390 | 229,694 | 11% |
| 合計 |  |  | 90 | 12,325 | 85,941 | 2,380,518 | 計 2,478,874 |

- reviewer・verifier は `~/.claude/agents/` の定義どおり（opus / high、haiku / medium）。上書きしていない
- main の effort は記録に残っておらず、分からない

## きっかけ

2026-10-13 にこのマシンで uvicorn を SIGTERM で止めたところ、
`analyzer/analysis.py` の `ProcessPoolExecutor`（spawn）が起動した gnubg の
子プロセスと `multiprocessing` の `resource_tracker` が、親を失ったまま残った。

## やったこと

- 面倒を見る範囲は、利用者と決めて **SIGTERM・Ctrl-C で正常に止めたときだけ**にした。
  親が SIGKILL で死んだときは対象外
- 原因: uvicorn（0.54）の `Server.capture_signals` は、正常に止めたあとで
  受けたシグナルを `signal.raise_signal` で投げ直す。プロセスはそのシグナルで
  死ぬので atexit が走らず、`ProcessPoolExecutor` が閉じられない
- `analyzer/analysis.py` に `shutdown()` を足し、`analyzer/app.py` の FastAPI の
  lifespan の終了処理から呼ぶようにした
- `analyzer/test_api.py` に `test_server_exit_stops_gnubg_helper` を足した
  （`TestClient` を `with` で使って lifespan を走らせ、終わったあとに子が生きていないことを見る）
- 作業は `local/todo-001` ブランチで行った（claude.ai のプロジェクト側の作業とぶつけないため）

## 確かめたこと

- 本物の uvicorn（port 8001）を SIGTERM で止めると、修正ありの 2 回は uvicorn と
  子 2 つが約 0.2 秒で消えた。修正を外した 1 回は、5 秒経っても子 2 つが残った
  （[verifier-report.md](../agents/TODO-001/verifier-report.md)）
- 足したテストは、修正を外すと落ちる（main が 1 回、reviewer が 2 通りで確かめた。
  [reviewer-report.md](../agents/TODO-001/reviewer-report.md)）。pytest は 8 passed

## 残ること

- Ctrl-C を 2 回押した強制終了（uvicorn の `force_exit`）では lifespan の終了処理が
  飛ばされる。そのときは atexit が走るはずだが、試していない
- `pytest` と `httpx` が `analyzer/requirements.txt` に無く、venv に手で入れた

## 分担の振り返り

- reviewer は指摘 0 件で、`force_exit` のときの扱いを対象外の補足として挙げた。
  verifier は修正の有無で子が残るかが変わることを実測した。どちらも、main が
  見落としていた問題は見つけていない
- 見込みとの食い違いは無かった。main の割合が 80% と大きいのは、サーバーを
  動かす前置きのやり取りが範囲に入ったため
- 次に同じ規模の項目（数ファイル・十数行で、終了時の挙動が変わるもの）をやるときも、
  同じく main が実装し、reviewer（Opus / high）のあとに verifier（Haiku）を回す。
  reviewer に修正を外したテストを試させると main の確認と重なるので、
  main が試したと書いたうえで、reviewer には「テストの形を読むだけ」と頼めば減らせる
