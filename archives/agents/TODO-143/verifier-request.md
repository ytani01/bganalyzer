# TODO-143 verifier への依頼

## 目的

ブランチ `claude/recognizer-dark-checkers` の 3 つの変更が、それぞれ壊すと読みが変わる（効いている）ことを実測で確かめる。コードは直さない（下の「一時的に壊す」は、確かめたら必ず `git checkout recognizer/` で戻す）。

## 測り方

作業ディレクトリ `/home/ytani/work/bganalyzer`。読み違いは次で出す（正解と違うポイントが `(ポイント, 正解, 読み)` で出る。`[]` は全部当たり）:

```
uv run -q python archives/agents/TODO-143/wrong_points.py <サンプル名> ...
```

全サンプルは流さない（CI で確認済み）。`check_accuracy.py` と `evaluate.py` を引数なしで流さない。

## 確かめること

1. **今のコードの読み**: `collected-galaxy-screen-7 commons-leather-cups photo-black-blue-oblique` を読む。期待: galaxy-screen-7 は `[]`、leather-cups は 9 か所の読み違い（16 は入らない）、black-blue-oblique は `[(19, -5, -4)]`
2. **t0480x を自動の四隅で読む**: `uv run python recognizer/board.py collected/user-1792344322479-t0480x.jpg --corners 232.3,333.8,1755.9,318.5,1768.3,1557.4,257.4,1587.6 --home right --bottom-colour 1` の出力の `"points"` が `[-1, 0, 0, 0, 0, 5, 0, 3, 0, -1, 0, -5, 5, 0, 0, 0, -3, 0, -5, 0, 0, 0, 0, 2]` か
3. **駒の色の画像を外す**: `recognizer/board.py` で `checker_lab = count_from_circles(...)` の行の右辺を `None` にして、galaxy-screen-7 を読む。期待: 読み違いにポイント 1 が出る。戻す
4. **弱い山から足すのを外す**: `recognizer/checkers.py` の `out += _weak_checkers(` の行を `out += []` にして、galaxy-screen-7 を読む。期待は決めていない。読み違いがどう変わったかをそのまま書く。戻す
5. **円と円の間を埋めるのを外す**: `recognizer/checkers.py` の `add_hidden_stacks` で、`deps = sorted(` の直前に `continue` を入れ、photo-black-blue-oblique を読む。期待: ポイント 19 の読みが -4 から変わる（-1 など）。戻す
6. **色の画像でだけ見つかった円の色の条件を外す**: `recognizer/checkers.py` の `continue   # found in checker colours' images only` の行の `continue` を `pass` にして、commons-leather-cups を読む。期待は決めていない。読み違いがどう変わったかをそのまま書く。戻す

最後に `git status --short` が空であることを確かめる。

## 報告

`archives/agents/TODO-143/verifier-report.md` に、項目ごとに「実行したコマンド・出力（読み違いの行）・期待どおりか」を書く。期待どおりのものは 1 行でよい。
期待と違ったときは、原因を探らず、出力をそのまま書いて「期待と違う」と報告する。境界線上の判断は報告だけにする。
返事は「終わったか・報告ファイルのパス・期待と違った項目」だけにする。
