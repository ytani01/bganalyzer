# TODO

**残っている項目: TODO-001、TODO-002。** これまでに 0 件を決着させた。
新しく足すときは「完了済み」の上に節を作る。**番号は `TODO-003` から。**

---

## TODO-001. サーバーを止めると gnubg の子プロセスが残る

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort medium | main（実装）+ reviewer（Opus / high）+ verifier（Haiku / medium） |

- [ ] 原因を確かめる（uvicorn の終了時に `_pool` が閉じられていないのか）
- [ ] 終了時に子プロセスも止める
- [ ] 止めたあとに子プロセスが残らないことを確かめるテストか手順を残す

2026-10-13 にこのマシンで uvicorn（PID 33917）を SIGTERM で止めたところ、
`analyzer/analysis.py` の `ProcessPoolExecutor`（spawn）が起動した
gnubg の子プロセスと `multiprocessing` の `resource_tracker` が、
親を失ったまま残った（手で kill した）。`analysis.py` にも `analyzer/app.py` にも、
終了時に `_pool` を `shutdown()` する処理は無い。

**着手前に決めること:** どこまで面倒を見るか。

- 選択肢: (a) SIGTERM・Ctrl-C で正常に止めたときだけ（FastAPI の lifespan で
  `_pool.shutdown()`）／(b) 親が SIGKILL で死んだときも子が自分で終わる
  （親の死を子の側で検知する）
- いつ聞くか: 着手するとき（`~/.claude/CLAUDE.md` の「子プロセスやシグナルを
  扱う項目」）

---

## TODO-002. PWA と API の公開先を決める

PWA と API は `Dockerfile` で1つのコンテナになっている（ステップ3）。スマホからいつでも使うには、
HTTPS で常駐できるホスト（コンテナを動かせる PaaS や VPS）に置く必要がある。gnubg の都合でサーバーレス関数は不可、
ワーカーは1つ。どこに置くかは ai1 が決める。決まったら HTTPS 終端と `docker run` の手順を README に書く。

---

## 完了済み

決着した項目は `archives/todo/` にある（1 項目 1 ファイル）。
一覧は [archives/index.md](archives/index.md)（新しい順）。やらないと決めたものは
ファイル名に（対応しない）が付いていて、理由も書いてある。蒸し返す前に読むこと。
