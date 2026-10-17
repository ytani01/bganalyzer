# TODO-114 確認の報告（verifier）

対象: `recognizer/import_collected.py`（未追跡のため `git diff` には出ない）と `analyzer/test_collected.py`。コードは直していない。

## 1. テスト（壊す前の状態）

`timeout 120 uv run pytest -q analyzer/test_collected.py < /dev/null`

```
........                                                                 [100%]
8 passed in 5.02s
EXIT=0
```

## 2. 壊すと落ちるか

`recognizer/import_collected.py` の元の sha256 は `f32c3f21…d977`。壊すたびに同じ `pytest` を流し、後で元のファイルを戻した。戻した後の sha256 は両方とも `f32c3f21…d977`（一致）。

(a) `merge()` の checks 判定を `if True:` に変える（`if "no checks reported" not in checks.stderr:` の行を置き換え）。

```
.......F
____________________ test_import_merges_on_the_latest_main _____________________
>       assert [a[1] for a in calls].count("checks") == 3 and logs == ["u: merged"]
E       AssertionError: assert (1 == 3)
FAILED analyzer/test_collected.py::test_import_merges_on_the_latest_main
1 failed, 7 passed in 5.32s
EXIT=1
```

(b) `gh("pr", "merge", url, "--merge", "--match-head-commit", sha)` の `sha` を `"x"` に変える。

```
.......F
____________________ test_import_merges_on_the_latest_main _____________________
>       assert ("pr", "merge", "u", "--merge", "--match-head-commit", "b") in calls
E       AssertionError: assert ('pr', 'merge', 'u', '--merge', '--match-head-commit', 'b') in [...]
FAILED analyzer/test_collected.py::test_import_merges_on_the_latest_main
1 failed, 7 passed in 5.42s
EXIT=1
```

どちらの壊し方でも、狙った分岐を見ているテストが落ちた。

## 3. 本物の `collected/` の組で試す

`collected/` の `user-*.truth.json` は 23 組。mtime の古い順に先頭 3 組を選んだ。

- 選んだ 3 組: `user-1792130519864-ajxlol`, `user-1792157880159-a631li`, `user-1792157990387-xuz0xb`
- `pick(collected, 3組, s)`（s は空のフォルダ）の結果: 3 組すべて
- `add` で書けた組: `collected-ajxlol`, `collected-a631li`, `collected-xuz0xb`（jpg と truth.json の 2 ファイルずつ）

### 元の写真との突き合わせ（cv2）

| 組 | 元の写真の大きさ (h, w) | 書いた写真の大きさ | 盤の外で黒でない画素 | 盤の外で黒の割合 | 盤の内で黒の割合 |
|---|---|---|---|---|---|
| ajxlol | 1726 × 1439 | 一致 | 18440 | 98.45% | 0.01% |
| a631li | 1592 × 1728 | 一致 | 27468 | 96.55% | 0.01% |
| xuz0xb | 658 × 775 | 一致 | 1941 | 97.85% | 0.00% |

盤の外で黒でない画素は、どの組も盤の辺から 17.6 px 以内（ajxlol 17.6 px、a631li 16.0 px、xuz0xb 10.0 px）にあった。JPEG を書き直したときの縁のにじみと見てよいと思う（ただし推定）。

### truth.json の項目

- 元の項目名（14 個）と書いた項目名は 3 組とも一致し、落ちた項目はなし。
- 項目名: `bar_black, bar_white, bottom_colour, corners_TL_TR_BR_BL, cube, dice, fixed_points, home, image, note, off_black, off_white, points, read`
- `image` は `collected-<id>.jpg` に変わり、`note` が新しく入った（「Collected on the server (2026-10-17) and added automatically: the board as corrected by hand.」）。

### 画像を目で見た結果（1 枚ずつ）

- `collected-ajxlol.jpg`: 盤の外は黒。盤の中は欠けていない。盤の角の周りに余計なものは見えない。合っている。
- `collected-a631li.jpg`: 盤の外は黒。盤の中は欠けていない。合っている。
- `collected-xuz0xb.jpg`: 盤の外は黒。盤の中は欠けていない。合っている。

### 食い違い（報告が必要な点）

- **`ajxlol` は本物の `samples/` に既にある**（`samples/collected-ajxlol.jpg` と `.truth.json`）。今回の `pick` は空の s を渡したので、この重複を見ていない。
- 本物の `samples/` を相手に `pick` を読み取りだけで流すと、結果は `['user-1792157880159-a631li.truth.json', 'user-1792157990387-xuz0xb.truth.json']` になった。`ajxlol` は外れる。`pick` の判定は想定どおりに動いている。
- 本番の run は `wt / "samples"`（origin/main の samples）を渡すので、本番では `ajxlol` は外れる。今回の書き出しは確認用で、本番の挙動とは違う。

## 4. 確かめられなかったこと・判断が要ること

- `run()`・`_run()`・`collected.py` の実行、`BG_IMPORT` を付けたコマンド、git の push・PR、テスト全体、全サンプルの精度は、指示のとおり流していない。
- `merge()` の本番の動作（gh の実際の応答、PR の作成や merge）は、このテストと書いた画像からは確かめられない。
- 「盤の外の黒でない画素が縁から 17 px 以内」の原因は JPEG の再圧縮と推定。根拠は見た目と距離だけで、実害は未確認。
- 判断が要る点: 重複の扱い（`samples/` に既にある `ajxlol` を本番で外す挙動は想定どおりか。コードの読みでは外れる）。
- 作業中に使った一時ファイルは scratchpad にのみ置いた。リポジトリには、この報告ファイルと `archives/agents/TODO-114/` 以外に書いていない。
