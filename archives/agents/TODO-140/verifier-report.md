# TODO-140 確認報告（verifier）

ブランチ `claude/screen-number-rows`。コードは直していない。

## 1. 写真の四隅（t0480x）: 期待どおり

`cd recognizer && uv run python corners.py ../collected/user-1792344322479-t0480x.jpg` → 終了コード 0

```
[[232.3, 333.8], [1755.9, 318.5], [1768.3, 1557.4], [257.4, 1587.6]]
```

上の辺 y 318.5〜333.8、下の辺 y 1557.4〜1587.6。期待（上 318〜334、下 1557〜1588）どおり。

## 2. check_corners: 期待どおり

`uv run python check_corners.py ../samples/collected-m5ekpe.truth.json ../samples/synth-cube-photo4-4.truth.json ../samples/photo2.truth.json` → 終了コード 0

```
collected-m5ekpe               0.0%  0.56s
synth-cube-photo4-4            2.9%  0.65s
photo2                         1.6%  0.57s
within 3.6%: 3, further: 0, not found: 0
```

## 3. 壊すと戻るか（作業コピーを一時変更、測り終えて `git checkout recognizer/corners.py` で戻した）

| 変更 | t0480x の四隅 | m5ekpe（check_corners） | m5ekpe の四隅（corners.py） |
|---|---|---|---|
| なし（HEAD） | 期待どおり（上 318〜334、下 1557〜1588） | 0.0% | [[264.5, 173.9], [1865.9, 157.9], [1905.9, 1490.3], [251.2, 1506.8]] |
| (a) `INNER_OUT = 0.0` | [[239.6, 258.6], [1755.0, 228.3], [1769.1, 1640.6], [253.9, 1686.0]]（上 228〜259、下 1641〜1686。番号の行に戻った） | 4.4%（3.6% を超えて外れた） | 測らず |
| (b) `SWAP_GAIN = 0.0` | 変わらず（期待どおり上 318〜334、下 1557〜1588） | 5.6%（外れた） | [[273.0, 173.8], [1751.2, 159.0], [1924.4, 1490.1], [246.3, 1506.9]] |

- (a): 期待どおり。t0480x は番号の行まで囲む元の値に戻り、m5ekpe も外れた。
- (b): 期待どおり。m5ekpe の右の辺は上端 x 1866→1751、下端 x 1906→1924 となり、上下の x のずれが約 40px から約 173px に広がった（斜めになった）。m5ekpe は外れた。
- t0480x は (b) で変わらなかった。SWAP_GAIN は m5ekpe の側だけに効いている。

後始末: `git checkout recognizer/corners.py` を 2 回実行し、`git status --short` は空（差分なし）。作業中に作った退避コピーも削除した。

## 4. pytest（リポジトリのルート）: 通る

`uv run pytest analyzer/test_api.py -k corners` → 終了コード 0

```
collected 50 items / 43 deselected / 7 selected
analyzer/test_api.py .......  [100%]
7 passed, 43 deselected, 1 warning in 23.90s
```

warning は fastapi の testclient の httpx 非推奨の表示で、TODO-140 とは関係がない。

## 変更ファイルについて

`git diff main...HEAD --stat` の変更は次のとおり（今回の確認の対象は `recognizer/corners.py` と、その挙動に関わるテストと結果だけ）。

- `recognizer/corners.py`（指示の範囲: `_swap` の内側へ移す分岐、`SWAP_GAIN`、`INNER_OUT`/`INNER_IN`/`OUT_DROP` の追加）
- `TODO.md`、`docs/corners.md`、`recognizer/README.md`、`recognizer/accuracy_baseline.json`、`recognizer/board.py`、`samples/collected-m5ekpe.truth.json`、`archives/agents/TODO-140/reviewer-report.md`

指示は「文書・版・accuracy_baseline.json は見なくてよい」なので、これらの中身は確かめていない。`recognizer/board.py`（版の変更と思われる）と `samples/collected-m5ekpe.truth.json` の 1 行変更は、指示の範囲に入るか判断していない。管理者が差分を見て決めること。

## 確かめられなかったこと・判断できないこと

- 全サンプルの精度は流していない（指示どおり。CI の accuracy が見る）。
- m5ekpe の (a) の四隅は測っていない（期待は「外れる」で、check_corners の 4.4% で外れたことは確かめた）。
- 境界線上の判断はしていない。実害の範囲（他のサンプルへの影響）は未確認。
