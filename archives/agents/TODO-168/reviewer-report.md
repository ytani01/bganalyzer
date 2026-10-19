# TODO-168 reviewer の報告

対象: PR #502（`origin/main...33df9e5`、6 コミット）。

## 要修正

なし。

## 検討

### 1. CLAUDE.md のマージの条件と HANDOVER.md の CI の節に `ruff` が無い

- `CLAUDE.md:11` 付近（コマンド）、`CLAUDE.md` の「共同開発」の「マージの直前に…`test` が通ってからマージする（`accuracy` が走った PR はそれも）」、`docs/HANDOVER.md:111-113`（CI）
- ジョブ `ruff` を足したが、マージの条件は `test`・`accuracy` しか挙げていない。書かれたとおりに進めると、
  `ruff` が落ちていてもマージしてよいことになる（CI に required check の設定があるかは未確認）。HANDOVER.md の CI の節も
  `test` と `accuracy` だけを説明している。コマンドの一覧にも `uv run ruff check` / `uv run ruff format` が無い。
- 根拠: `rg -i ruff` を `archives/`・`uv.lock`・`*.py` の外にかけると、出てくるのは `TODO.md` と `pyproject.toml` だけ。

### 2. isort の first-party は `known-first-party` より `src` のほうが手間が少ない

- `pyproject.toml:34`（`[tool.ruff]`）
- 今は `recognizer/board.py` で `import cube as cube_reader` / `import cv2` / `import dice as dice_reader` / `import exact` /
  `import numpy as np` が 1 つの塊に混ざっている（HEAD で確認）。
- `known-first-party` にすると `recognizer/` のモジュール名（20 近く）を並べることになり、モジュールを足すたびに直す必要がある。
  `[tool.ruff]` に `src = [".", "recognizer", "analyzer", "tools"]` の 1 行を足せば、ruff がディレクトリから first-party を見分ける。
  HEAD のコピーにこの 1 行を足して `ruff check --select I` をかけると、I001 が 34 件出た（並べ替えが 34 ファイルに入る）。
- 入れるかどうかは判断が要る（差分が増える。入れないなら今のままで実害は無い）。

## 好みの範囲

- `recognizer/radial.py:29` のコメント `((O / cap)^2 in Loy and Zelinsky)` は、改名前の変数 `O` と同じ字。論文の記号として読めるので直さなくてもよい。

## 問題の無かった点

- 設定: `select = ["E", "F", "I"]`、`ignore = ["E501"]`、`extend-exclude = ["archives"]`、行の長さは既定（`line-length` の指定なし）。`extend-immutable-calls` は無い。
- E・F・I 以外の規則のための変更: 無い。差分の `noqa`・`round(`・`check=`・`with open` を `rg` で探すと、出てきた行は折り返しと空白だけ。`# noqa: BLE001`（`analyzer/`）と `# noqa: E731`（`test_*.py`）は main からあったもの。
- 整形のコミット 68b79cd: 5cc9bad の木に `ruff format` をかけた結果と `diff -r` で完全に一致した（整形以外の変更は無い）。
- 自動修正のコミット c652e27: 68b79cd の木に `ruff check --fix` と `ruff format` をかけた結果と完全に一致した。
- 1732be9 の手で直した分（E731・E741）:
  - E731 の 11 件は、どれも同じ名前の `def` にしていて、引数（`*a`、`cwd=REPO` の既定値を含む）・戻り値は同じ。ループの中の `gh`（`test_collected.py`）は lambda と同じく `failing` を呼ばれたときに読む。
  - E741: `l`→`m33`（`exact.py`・`test_exact.py`）、`O`→`orient`（`radial.py`、関数の中だけ）、内包表記の `l`→`ln`。改名漏れは無く、名前はほかの名前とぶつからない（`rg` で確認）。`ruff check` が通るので F821 も無い。
- `uv run ruff check` と `uv run ruff format --check` は HEAD で通る。
- `.github/workflows/ruff.yml`: `test.yml` と同じ書き方（`checkout@v4`・`setup-uv@v6` の `enable-cache`・`uv sync --frozen`・`uv run`）。`push` は main で毎回、`pull_request` は `**.py`・`pyproject.toml`・`uv.lock`・ワークフローの変更で走る。どちらのコマンドも違反があれば 0 以外で終わる（実際に CI で落ちるかは verifier が見る）。
- 版を上げていないのは CLAUDE.md の「バージョン」どおり（挙動が変わらないため）。

## 作り込みすぎ

なし。
