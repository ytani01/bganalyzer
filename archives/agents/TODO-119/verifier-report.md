# TODO-119 確認報告

方法: `~/.claude/hooks/full-run-guard.py` に `{"tool_input":{...},"cwd":"/home/ytani/work/bganalyzer"}` を標準入力で渡して実行（スクリプトは scratchpad の t.py。対象コマンドは実行していない）。出力に `ask` があるかを見た。終了コードはすべて 0。

| 例 | 期待 | 結果 |
|---|---|---|
| uv run python recognizer/check_accuracy.py | ask | ask |
| .venv/bin/python3 recognizer/check_accuracy.py | ask | ask |
| uv run python recognizer/evaluate.py | ask | ask |
| python3 -u recognizer/evaluate.py --app | ask | ask |
| cd recognizer && python evaluate.py --slots | ask | ask |
| sed -n 40,80p recognizer/check_accuracy.py | なし | なし |
| rg -n main recognizer/evaluate.py | なし | なし |
| uv run python recognizer/check_accuracy.py --update | なし | なし |
| uv run python recognizer/evaluate.py samples/photo2.truth.json | なし | なし |
| git log -- recognizer/check_accuracy.py | なし | なし |
| 依頼文(prompt)に `uv run python recognizer/check_accuracy.py` | ask | ask |

食い違い: なし。
git status: 検証開始時点でクリーン（確認中に変更なし。報告ファイルのみ追加）。
確かめなかったこと: 上記以外の書き方（例: `python -m`、改行をまたぐ依頼文）。
