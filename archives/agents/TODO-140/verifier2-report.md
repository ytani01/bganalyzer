# TODO-140 確認 2（verifier2）

ブランチ `claude/dark-checkers-screen`。対象は `recognizer/colours.py` と `recognizer/board.py`（`git diff main...HEAD`）。コードは変更していない。

## 1. 期待値の確認（評価）

コマンド: `uv run python recognizer/evaluate.py collected/user-1792344322479-t0480x.truth.json samples/collected-w8eaks.truth.json`（終了コード 0）

- t0480x: 21/24, bar ok。違うのはポイント 1（truth -1 / got +0）、12（truth -5 / got +0）、19（truth -5 / got +0）。期待どおり。
- w8eaks: 23/24, bar ok。違うのはポイント 19（truth -5 / got -1）。期待どおり。

## 2. 壊すと戻るか（変更後に `git checkout recognizer/colours.py` で戻し、`git status` が空であることを確認済み）

- (a) `AVOID_DE = 0` にした場合: t0480x は 20/24。違うのはポイント 1、12、17（truth -3 / got +0）、19。期待どおり（ポイント 17 が増える）。
- (b) `tri = t[::-1] if swap else t` を `tri = t` にした場合: w8eaks は `bar wrong`（23/24、ポイント 19 のみ違う）。期待どおり（bar が wrong になる）。

## 3. pytest

`uv run pytest analyzer/test_api.py -k recognize -q`: 50 deselected、0 selected、終了コード 5（テストが 0 件）。
`analyzer/test_api.py` の 50 件のどれも `recognize` の名前にマッチしない。手順どおり `-k` は外さず、ここで止めた。
`-k` を外したときに何が走るかは確かめていない。このテストが recognize を通すかは、この確認からは判断できない。

## 判断が要る点

- 項目 3 で `recognize` に一致するテストが無い。対象のテストが別ファイルにあるのか、`-k` の語が違うのかは分からない。管理者が判断する。
- 実害は未確認（項目 3 の範囲について）。
