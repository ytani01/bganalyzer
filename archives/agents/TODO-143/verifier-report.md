# TODO-143 verifier 報告

作業ディレクトリ `/home/ytani/work/bganalyzer`、ブランチ `claude/recognizer-dark-checkers`。
すべて `uv run -q python archives/agents/TODO-143/wrong_points.py <サンプル名>` で読み違いを出した。

## 1. 今のコードの読み

実行: `wrong_points.py collected-galaxy-screen-7 commons-leather-cups photo-black-blue-oblique`（終了コード 0）

```
collected-galaxy-screen-7 []
commons-leather-cups [(7, 0, 3), (8, 3, 0), (12, -5, 0), (13, 5, 0), (14, 0, 5), (15, 0, -1), (17, -3, 0), (19, -5, -2), (22, 0, -1)]
photo-black-blue-oblique [(19, -5, -4)]
```

期待どおり。leather-cups は 9 か所で、16 は入っていない。

## 2. t0480x を自動の四隅で読む

実行: `recognizer/board.py collected/user-1792344322479-t0480x.jpg --corners 232.3,333.8,1755.9,318.5,1768.3,1557.4,257.4,1587.6 --home right --bottom-colour 1`（終了コード 0）

```
"points": [-1, 0, 0, 0, 0, 5, 0, 3, 0, -1, 0, -5, 5, 0, 0, 0, -3, 0, -5, 0, 0, 0, 0, 2]
```

期待の配列と完全に一致。

## 3. 駒の色の画像を外す

変更: `recognizer/board.py` 153 行目の右辺を `None` にした（`checker_lab = None`）。
実行: `wrong_points.py collected-galaxy-screen-7`（終了コード 0）

```
collected-galaxy-screen-7 [(1, -1, 0), (12, -5, 0), (19, -5, 0)]
```

期待どおり、ポイント 1 が出た。`git checkout -- recognizer/board.py` で戻した。

## 4. 弱い山から足すのを外す

変更: `recognizer/checkers.py` 298 行目を `out += []` にした。
実行: `wrong_points.py collected-galaxy-screen-7`（終了コード 0）

```
collected-galaxy-screen-7 []
```

読み違いは変わらず 0 件（元も 0 件）。期待は決めていないので、この結果をそのまま書く。
`git checkout -- recognizer/checkers.py` で戻した。

## 5. 円と円の間を埋めるのを外す

変更: `recognizer/checkers.py` の `deps = sorted(`（381 行目）の直前に `continue` を入れた（インデントは 12 スペース）。
実行: `wrong_points.py photo-black-blue-oblique`（終了コード 0）

```
photo-black-blue-oblique [(19, -5, -1)]
```

期待どおり。ポイント 19 の読みが -4 から -1 に変わった。`git checkout -- recognizer/checkers.py` で戻した。

## 6. 色の画像でだけ見つかった円の色の条件を外す

変更: `recognizer/checkers.py` 242 行目の `continue   # found in checker colours' images only` の `continue` を `pass` にした。
実行: `wrong_points.py commons-leather-cups`（終了コード 0）

```
commons-leather-cups [(7, 0, 3), (8, 3, 0), (12, -5, 0), (13, 5, 0), (14, 0, 5), (15, 0, -1), (16, 0, -1), (17, -3, 0), (19, -5, -2), (22, 0, -1)]
```

読み違いは 9 か所から 10 か所になり、新たに (16, 0, -1) が加わった。ほかの 9 か所は変わらない。
期待は決めていない。`git checkout -- recognizer/checkers.py` で戻した。

## 最後の確認

各変更の後に `git checkout --` で戻したので、`git diff --stat` は空。`git status --short` は `?? archives/agents/TODO-143/` だけ。
recognizer/ に変更は残っていない。

## 確かめられなかったこと

- 全サンプルの読みは流していない（依頼どおり）。
- 項目 4 の「弱い山」の外し方は、galaxy-screen-7 以外のサンプルでは見ていない。
- 判断が要る点は無い。
