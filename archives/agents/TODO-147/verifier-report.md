# TODO-147 確認の報告（verifier）

対象: `git diff 1aa69e8 HEAD`（HEAD = 51522e1）

## 1. `uv run pytest -q analyzer/test_collected.py`

- 結果: 通過。終了コード 0。
- 出力: `12 passed in 9.33s`

## 2. テストが壊すと落ちるか（stderr の行を戻す）

- `recognizer/import_collected.py` の `log(f"failed: {e!r}" + ...)` を `log(f"failed: {e!r}")` に一時的に戻し、`-k stderr` で実行。
- 結果: 落ちた。終了コード 1。
- 出力の要点:
  ```
  FAILED analyzer/test_collected.py::test_import_logs_the_end_of_stderr
  >       assert "line 29" in log and "line 10" in log and "line 9\n" not in log
  E       assert ('line 29' in "2026-10-19 12:20 failed: CalledProcessError(1, ['check_accuracy.py'])\n")
  1 failed, 11 deselected in 0.22s
  ```
- 後始末: `git checkout recognizer/import_collected.py`（`Updated 1 path from the index`）。`git status --short` は `?? archives/agents/TODO-147/` のみで、ファイルは HEAD に戻っている。

判定: 狙った分岐（stderr の末尾を残す行）を、テストが見ている。

## 3. `--jobs=` の解釈（`check_accuracy.main()`）

`measure_all` を、受け取った `jobs` を出して例外で止める関数に差し替え、実際の測定は流していない。

- `sys.argv = ["x"]` の場合: `measure_all received jobs = None`
- `sys.argv = ["x", "--jobs=2"]` の場合: `measure_all received jobs = 2`

判定: 指示どおり、None と 2 になる。

## 変更されたファイル（指示の範囲との照合）

`git diff --stat 1aa69e8 HEAD`:

| ファイル | 変更 | 範囲 |
|---|---|---|
| TODO.md | 5 行 | TODO-147 の節（指示の範囲内） |
| analyzer/test_collected.py | +13 | テストの追加（範囲内） |
| recognizer/check_accuracy.py | +1 行（ヘルプ）、`main()` の `--jobs=` 受け取り | 範囲内 |
| recognizer/import_collected.py | stderr の末尾を残す、`--jobs=2` 付きで呼ぶ | 範囲内 |

指示に無いファイルの変更は無い。`CLAUDE.md` のバージョン規則（recognizer の `__version__` を上げる）に関わる変更は、このコミット範囲の diff には含まれていない。上げるかどうかは判断していない。

## 確かめられなかったこと・判断できなかったこと

- テスト全体は流していない（指示どおり）。精度の測定も流していない。
- `--jobs=` の値が、実際の並列数（ProcessPoolExecutor の挙動）に効くかは見ていない。見たのは `main()` から `measure_all` への受け渡しだけ。
- 判断が要る点は報告だけ。特に無し。
