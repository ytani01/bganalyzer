# TODO-146 確認報告（verifier）

ブランチ: claude/collected-remove-imported（`git diff main...HEAD`）

## 1. `uv run pytest -q analyzer/test_collected.py`

- 出力: `...........  [100%]` / `11 passed in 17.50s`
- 終了コード: 0

## 2. remove() の実動作（scratchpad の一時ディレクトリ）

入力: `user-1-aaa.jpg`, `user-1-aaa.truth.json`, `user-1-aaab.jpg`, `user-1-aaab.truth.json`, `report.md`, `import.log`
実行: `ic.remove(Path(dir), ["user-1-aaa.truth.json"])`（`python -I` で recognizer/ を sys.path に入れて呼び出し）
残ったファイル: `['import.log', 'report.md', 'user-1-aaab.jpg', 'user-1-aaab.truth.json']`
終了コード: 0

期待どおり、user-1-aaa の 2 つだけが消えた。user-1-aaab と report.md・import.log は残った。

## 3. docs/raspi.md の TODO-146 の書き足しと実装の読み比べ

- docs/raspi.md 218 行目: 「マージされたら、取り込んだ組の写真と正解を `collected/` から消します（PR が開いたままなら残す。TODO-146）。」
- 実装（recognizer/import_collected.py `_run`）: `if merge(url, gh, log):` の中で `remove(d, todo)` と `log(...)`。`merge` は `merged.returncode == 0` のときだけ True を返し、チェック失敗・main とぶつかった・マージ失敗のときは False（`return log(...)` は None なので偽）。
- 判断: 食い違いなし。PR が開いたままなら消さない、という説明と合う。

## 補足（確認範囲の外、報告のみ）

- `remove()` は `n.removesuffix(".truth.json") + ".*"` で glob する。`pick` が返す名前が `.truth.json` のものだと前提している（`pick` は `names` の `*.truth.json` から選ぶ想定。今回の確認では `pick` の戻り値の形までは実行していない）。
- TODO.md の `[x]` は main 側の実装時点で入れられており、確認済みかは本報告が根拠。

## 判断が要る点

なし。
