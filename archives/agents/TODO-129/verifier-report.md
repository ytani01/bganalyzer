# TODO-129 確認報告（verifier）

1. `uv run pytest analyzer/test_pwa.py -q` は通る。26 passed（終了コード 0）。
2. 壊すと落ちる。result.js の `let out = ""` を `` `<p class="summary">${esc(r.summary)}</p>` `` に一時的に戻すと、`test_result_html` が落ちる（1 failed, 25 passed）。落ちた箇所は `analyzer/test_pwa.py:177`、`assert at == sorted(at) and at[0] == 0 and "手前が有利" not in html` で、`at` の先頭が 28（0 のはず）。元に戻したあと、保存しておいたコピーと `cmp` で一致（IDENTICAL）を確かめた。`git diff analyzer/static/result.js` は変更前と同じ内容。
3. 版は両方 "0.73.0"。`analyzer/app.py:33` の `__version__` と `analyzer/static/app.js:14` の `APP_VERSION`。

判断が要る点: なし。
