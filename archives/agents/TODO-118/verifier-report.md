# TODO-118 確認報告（verifier）

対象: claude/todo-118 のコミット ac8315e（fix(analyzer): 読み上げの「方が」を「ほうが」にする）

## 項目ごとの結果

1. `uv run pytest analyzer/test_pwa.py`: 通った。25 passed、終了コード 0。
2. `result.js` の `speechText` に「方」が残っていない: 確認。`rg 方 analyzer/static/result.js` で残るのは 77 行目（「ダブルせずギャモンを狙う方がよい局面」、表の文言）だけ。speechText（103〜133 行目）の 113・114 行目は「ほうが」。
3. テストが壊すと落ちるか: 落ちた。114 行目を「しない方が」に戻して実行し、`FAILED analyzer/test_pwa.py::test_speech_reads_who_rolls_next_first`、`1 failed, 24 passed`。`AssertionError` は `out["noDouble"]` の `startswith("白はまだダブルしないほうがよいです。")` で発生（出力: `'白はまだダブルしない方がよいです。白がかなり有利です。…'`）。pytest の終了コードは zsh で取り損ねた（PIPESTATUS の書き方が合わなかった）。失敗のサマリーから 1 と推定するが、コードの値そのものは未確認。復元後は `git checkout analyzer/static/result.js` で `Updated 1 path from the index`、`git status --short` は空、114 行目の「しないほうが」は 1 件に戻っている。
4. バージョン: `analyzer/app.py` の `__version__ = "0.65.1"`、`analyzer/static/app.js` の `APP_VERSION = "0.65.1"`。一致。

## 変更ファイル（ac8315e、HEAD~1 との比較）

- `analyzer/static/result.js`: 113・114 行目の 2 行だけ（「方がよいです」→「ほうがよいです」、「しない方が」→「しないほうが」）。指示の範囲内。
- `analyzer/test_pwa.py`: 107 行目付近の `tooGood` と `noDouble` の期待値の 2 行だけ。テストの期待を同じ文言に合わせたもの。範囲内。
- `analyzer/app.py`: `__version__` の 1 行（0.65.0→0.65.1）。範囲内。
- `analyzer/static/app.js`: `APP_VERSION` の 1 行（0.65.0→0.65.1）。範囲内。
- `TODO.md`: 1 行（TODO-118 の「直す」のチェックを入れた分）。範囲内。

作業ツリーは確認の前後とも clean。`archives/agents/TODO-118/verifier-report.md` だけを新しく作った。

## 確かめられなかったこと

- 読み上げの音（Google の読み上げで「かた」と読まれないこと）は、指示どおり確かめていない。項目の「スマホ」の行は未チェックのまま。
- テスト全体、画面の操作、精度は対象外。
- 項目 3 の pytest の終了コードは未記録（上記）。
- 判断が要る点は無い。
