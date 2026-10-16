# TODO-066 の実装依頼（implementer）

目的: 解析にマッチの長さ・両者のスコア・クロフォードを使えるようにし、PWA の 4 画面のどこでも直せるようにする。
TODO.md の TODO-066 と、`archives/agents/TODO-066/README.md` の「main の下調べ」を先に読むこと（gnubg の渡し方は測ってある。測り直さなくてよい）。

## やること

1. API: `AnalyzeRequest`（`analyzer/models.py`）と `/analyze-photo` の Form に、マッチの長さ（0 か省略 = マネー）・white と black のスコア・クロフォードを足す。
   不正な値（スコアが長さ以上、クロフォードなのに誰も N-1 でない など）は 422/400 で返す（今の cube の検証と同じ書き方で `analysis.py`）。
2. engine: `evaluate`・`find_best_moves`・`_complete_moves` の `gnubg.cube_info()` にマッチを渡す（スコアは手番側を先に）。
   `_cube_hint` はマッチを gnubg のコマンドで作り、マネーに戻すときは `new session`。クロフォードで「ダブルできない」は今の None と同じ扱い。
   同じ状態を毎回作り直す無駄は気にしなくてよい（正しさが先）。
3. 解析結果と読み上げ（`summary_ja` など）に、マッチならスコアを出す（例「7 ポイントマッチ 3-5（クロフォード）」）。マネーは今のまま。
4. PWA: 4 画面すべてで見えて直せる共通の場所（ヘッダーの中など、`index.html` の `<header>` 付近）に、1 つの部品で置く。
   - 初期値は前回の値（`app.js` の `keep`／読み出しと同じ try/catch で localStorage）。マネーに戻せる
   - 解析結果の画面で直したら解析し直す（`app.js` 1015 行付近の `if (state.result) analyze();` と同じ流れ）
   - 写真からの解析（`/analyze-photo`）にも渡す
5. テスト: `analyzer/test_api.py`・`test_pwa.py` に、マッチとマネーで答えが変わること、検証が弾くこと、クロフォードでダブルの判断が出ないことを足す。
   **壊すと落ちる**ことを 1 つは自分で確かめる（例: スコアを渡さないようにすると落ちる）。
6. `analyzer/README.md` の API の説明と、版（`analyzer/app.py` の `__version__` と `analyzer/static/app.js` の `APP_VERSION`）を 0.x.0 上げる（機能の追加）。
   `docs/PI_CHECKS.md` に、Pi の PWA でスコアを入れて解析できるかの項目を 1 つ足す（書式はそのファイルの決まりどおり）。

## 変えないもの・保つもの

- マネーゲームの答え（今のテストの期待値）は変えない。ジャコビー・ルールはマネーだけ
- gnubg は helper プロセスのメインスレッドだけで動かす（`engine.py` の作り）
- 白黒の呼び方（white = 手前）。スコアは white/black で受け、engine に渡すときに手番側を先にする
- テストは変えたファイルだけ `uv run pytest analyzer/test_<名前>.py` で流す（全体は CI）

## 完了条件と報告

- 上のテストが通る。コミットはしない（main がする）
- 報告は `archives/agents/TODO-066/implementer-report.md` に、変更点・流したテストとその結果・残る懸念だけ書く
- 返事は「終わったか・報告ファイルのパス・判断が要る点」だけ
