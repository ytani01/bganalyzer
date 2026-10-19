# TODO-168 implementer の報告

## 設定

`pyproject.toml`: dev 依存 `ruff>=0.17.1`、`[tool.ruff] extend-exclude = ["archives"]`、`[tool.ruff.lint] select = ["E", "F", "I"]`・`ignore = ["E501"]`。行の長さは既定の 88。
（最初は ruff の既定の規則で直したが、方針が E・F・I に変わったので、コミットを作り直した。既定の規則だけの直し〔`with open`・`check=False`・`round()` など〕は入っていない。）

## 変更（コミット）

1. ruff の追加と設定（`pyproject.toml`・`uv.lock`）
2. `ruff format` だけ（46 ファイル）
3. `ruff check --fix`（safe）: I001 が 38、E401 が 8、F401 が 2（使われていない `import cv2` など）
4. 手で直す指摘: E731（lambda の代入）11 件と E741（紛らわしい変数名）7 件
5. `.github/workflows/ruff.yml`（`uv run ruff check` と `uv run ruff format --check`。`.py`・`pyproject.toml`・`uv.lock` の変更で走る）、`TODO.md`、この報告

## (4) の一覧（noqa は 0 か所。挙動は同じ）

| 規則 | 件数 | 直し方 |
|---|---|---|
| E731 | 11 | `def` に書き換え（`ruff --unsafe-fixes`）。`analyzer/test_collected.py`・`test_ui_snapshot.py`、`recognizer/collected.py`・`import_collected.py`（8 か所）。呼び方も中身も同じ。`test_ui_snapshot.py` の古い `# noqa: E731` は外した |
| E741 | 7 | `l`→`m33`（行列の要素。`recognizer/exact.py`・`analyzer/test_exact.py`）、`l`→`ln`（`import_collected.py` の内包表記 2 か所）、`O`→`orient`（`recognizer/radial.py`、関数の中だけ） |

もとからある `# noqa: E731`・`# noqa: E402` は、今の規則で使われているのでそのまま残してある。

## 検証

- `uv run ruff check` 通る、`uv run ruff format --check` 57 ファイルとも整形済み
- pytest（1 ファイルずつ）: `test_collected`（12）、`test_exact`（6）、`test_ui_snapshot`（3）、`test_side`（17）、`test_tune`（3）、`test_photo_view`（12）、`test_pwa`（35）、`test_api`（51）すべて通った
- `test_api.py::test_version_reports_both_parts_and_commit` は worktree では落ちる（`.git` がファイルなので `git_commit()` が None を返す）。今回の変更とは無関係
- `check_accuracy.py`・`evaluate.py` と、テスト全体は流していない（CI に任せる）

## 版

挙動は変わらないので、analyzer・recognizer の版は上げていない。

## 残る懸念

- isort の既定では `recognizer/` の自作モジュール（`cube`・`dice`・`exact` など）が third-party と区別されず、`import cv2` や `numpy` と同じ塊に並ぶ。`known-first-party` を足せば分けられるが、設定を増やすので入れていない。
- I001 の並べ替えと F401 の削除は recognizer の import に入る。読み取りの結果は変わらないはずなので、CI の accuracy で確認してほしい。
- CI のジョブがわざと違反を入れた差分で落ちることは、まだ見ていない（verifier が見る）。
