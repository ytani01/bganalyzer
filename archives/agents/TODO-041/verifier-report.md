# TODO-041 verifier report

変更ファイル: TODO.md, analyzer/test_api.py のみ（git status）。差分は test_api.py に pytest import、shutil.which("git") が None なら pytest.skip を追加しただけ。

共通: img=$(docker compose images -q app | head -1)、コンテナは `--entrypoint sh -v "$PWD":/repo:ro -w /repo`、`pip install --target /tmp/dev pytest httpx` のあと `PYTHONPATH=/tmp/dev python -m pytest -q -rs -p no:cacheprovider ...`

1. git 無し: `... analyzer/test_api.py -k version_reports`
   -> `SKIPPED [1] analyzer/test_api.py:142: git is not installed` / `1 skipped, 34 deselected, 1 warning in 0.93s`
2. 偽 git（/tmp/fakegit/git が `echo 0000000`、-v /tmp/fakegit:/fakegit:ro、PATH=/fakegit:$PATH）:
   -> `AssertionError: assert '7393224' == '0000000'` / `1 failed, 34 deselected, 1 warning in 1.28s`
   skip されず比較が走り、壊すと落ちる。（最初の実行は -v の引数の組み立てミスで docker が起動せず、やり直した）
3. analyzer 全体（git 無し）:
   -> `FAILED analyzer/test_api.py::test_corners_are_found_on_samples` / `1 failed, 43 passed, 8 skipped, 1 warning in 88.93s`
   失敗はこの 1 件のみ（原因は調べていない）。skip 8 件は git 1 件と Node.js 7 件。

判断が要る点: なし。
