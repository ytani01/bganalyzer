# TODO-142 確認報告（verifier）

対象: ブランチ `claude/sample-names`（HEAD `8edf1f7`）。コードは変更していない。

## 1. 写真と正解の対応（`samples/*.truth.json`、top 直下の 76 件、external/ は除外）

`python -I` で `image` の値を読み、ファイルの存在と stem の一致を確かめた。
- 件数: 76
- 食い違い: 0 件（`image` の欠落、写真の不在、stem の不一致は無し）

## 2. `accuracy_baseline.json` のキーと stem の集合

- baseline のキー: 76、正解ファイルの stem: 76
- baseline のみ: なし / 正解のみ: なし。一致

## 3. 旧名の残り

`rg -n` を指示どおりのパターンで実行（`-g '!archives/**'`）。終了コード 0。出力は 4 行。

```
./TODO.md:68:2026-10-19 ユーザーの依頼。`samples/` の名前（`collected-2aunci` など）が分かりにくいので、…
./TODO.md:69:範囲は全部（collected-*・photo2〜6・screen1・2・tv-vegas-open・commons-*・synth-*・external）。
./recognizer/README.md:87:  TODO-073 で、ほかのサンプルと同じ写真だった collected-s5dd7x・collected-h8ilqt を消した（…）
./recognizer/README.md:537:試して採らなかったもの: 列ごとに…（中央に模様のある盤 collected-h8ilqt（TODO-073 で消した…）…
```

TODO.md の 68〜69 行と、README の削除済みサンプル（s5dd7x・h8ilqt）だけ。指示どおり。食い違いなし。

## 4. テストが壊すと落ちるか（`analyzer/test_collected.py`）

変更は各回 `sed` で 1 行だけ。確認後は `git checkout -- recognizer/import_collected.py` で戻し、`git status --short` が空になったのを毎回確かめた。

| 変異 | 変更 | 結果 | 出力の要点 |
|---|---|---|---|
| a. pick | `added` を `(samples / f"collected-{sample_id(n)}.truth.json").exists()` に戻す | 落ちた（1 failed, 8 passed） | `test_import_skips_what_samples_has` の `assert ['user-1-aaa.truth.json'] == []` が失敗。`analyzer/test_collected.py:113` |
| b. free | `k = 2` を `k = 1` | 落ちた（1 failed, 8 passed） | `test_import_names_the_pair_as_claude_says`: `AssertionError: assert 'collected-blue-felt-top-1' == 'collected-blue-felt-top-2'`。`test_collected.py:158` |
| c. describe | `return last if NAME.fullmatch(last) else None` を `return last` | 落ちた（1 failed, 8 passed） | 同じ `test_import_names_the_pair_as_claude_says`: `assert 'collected-Bl...t, from above' == 'collected-ccc'`。`test_collected.py:158` |

3 回とも狙った分岐のテストが落ち、ほかの 8 件は通った。

注: b・c の出力を一時ファイルへ書いた。c の出力は `/tmp/claude-649/mut_c.log` に残っている（作業ディレクトリ外。不要なら消してよい）。b は `.mut_b.log` を作って消した。

## 5. 変更したテストファイルだけ

`uv run pytest -q analyzer/test_collected.py analyzer/test_photo_view.py analyzer/test_side.py analyzer/test_tune.py`
- 結果: `41 passed, 3 warnings in 75.37s`、終了コード 0
- warnings は fastapi の httpx 非推奨と multiprocessing の fork 警告。今回の変更とは関係しない

## 最後の確認

- 変異を戻したあと `git status --short` は空（`recognizer/import_collected.py` は HEAD と同じ）
- この報告ファイル `archives/agents/TODO-142/verifier-report.md` を作ったため、以後 `git status` には未追跡のこの 1 件だけ出る（指示で書いてよいとされたファイル）

## 確かめられなかったこと

- 名前の良し悪し、画像の中身は見ていない（指示どおり）
- テスト全体、`evaluate.py`、`check_accuracy.py` は流していない（指示どおり）
- 5 の変更ファイル以外のテストが、名前変更で壊れていないかは、この確認の範囲外
- 判断が要る点: 無し
