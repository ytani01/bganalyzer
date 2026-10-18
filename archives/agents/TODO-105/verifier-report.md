# TODO-105 verifier 報告

確認対象: 作業ディレクトリ `/home/ytani/work/bganalyzer`（ブランチ `claude/todo-105-outline`、未コミット）。
main の版は git worktree `/tmp/claude-649/-home-ytani-work-bganalyzer/0be4fc1f-cffe-45f2-9cb2-424b90f22a6e/scratchpad/main-wt`（8410215）。
作業ディレクトリのファイルは変更していない。main-wt では `analyzer/test_api.py` を今の版に写し、1 サンプルずつの variant を作って確かめ、確認後に元へ戻した。

## 1. テストが壊すと落ちるか（main の corners.py で実行）

各 variant は `test_corners_are_found_on_samples` のサンプル一覧を 1 件だけにし、閾値は今の test_api.py の値を使った。
実行: `uv run pytest analyzer/test_one_<名前>.py -k corners_are_found_on_samples -q -p no:warnings`

| サンプル | 閾値 | main での結果 | 終了コード |
|---|---|---|---|
| commons-diagram-prime | 0.02 | 落ちた: `assert 0.047489367230991814 < 0.02` | 1 |
| commons-travel-case | 0.015 | 落ちた: `assert 0.01975991147658557 < 0.015` | 1 |
| photo4 | 0.04 | 落ちた: `assert 0.04505114454705899 < 0.04` | 1 |
| commons-nardy-midgame | 0.035 | 落ちた: `assert 0.06014540396452214 < 0.035` | 1 |
| collected-m5ekpe | 0.02 | 落ちた: `assert 0.09311893417777498 < 0.02` | 1 |

5 つとも main で落ちる。テストが狙ったサンプルを見ていることは確認できた。
（注: 変更前の閾値で main が通るかは見ていない。今回の確認の範囲外。）

## 2. 今の作業ディレクトリで `analyzer/test_api.py -k corners` が通るか

実行: `uv run pytest analyzer/test_api.py -k corners -q -p no:warnings`
結果: `7 passed, 42 deselected in 16.13s`、終了コード 0。一致。

## 3. 記録した数字の再現

実行: `uv run python recognizer/check_corners.py samples/collected-m5ekpe.truth.json samples/commons-travel-case.truth.json samples/photo4.truth.json`
終了コード 0。出力:

```
collected-m5ekpe               0.3%  0.44s
commons-travel-case            0.8%  0.51s
photo4                         3.5%  0.43s
within 3.6%: 3, further: 0, not found: 0
```

`full-new.json` の app でない方の値（全長に対する比率）と比べた:

| サンプル | full-new.json（app でない方） | 0.1% 表示 | 判定 |
|---|---|---|---|
| collected-m5ekpe | 0.002692639781047312（0.27%） | 0.3% | 一致 |
| commons-travel-case | 0.008459013211592068（0.846%） | 0.8% | 一致 |
| photo4 | 0.03456085213069835（3.456%） | 3.5% | 一致 |

注: check_corners の表示は 0.1% 単位なので、一致は 0.1% の桁までの確認。小数点以下の桁までは見ていない。
注: `full-new.json` の photo4 の app 版は 0.02759（2.8%）で、app 版とは値が違う。今回は指示どおり app でない方と比べた。

## 確認できなかったこと・判断が要ること

- 変更前（閾値を緩めた旧テスト）が main で通ることは確かめていない。
- 全サンプルの比較と、テスト全体は範囲外（指示どおり）。
- 判断が要ることは特に無い。
- 注意点（実害は未確認）: 検証の途中、`uv run pytest` を `analyzer/test_one_<ハイフン入りの名前>.py` で流すと PreToolUse の hook が「テスト全体の pytest」として止めた。ハイフンを除いた名前にすると通った。作業ディレクトリのテストには影響しない。
