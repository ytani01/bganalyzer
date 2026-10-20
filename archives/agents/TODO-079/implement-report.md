# TODO-079 実装の報告

ブランチ `claude/dice-green-oblique`（コミット af6a0e7、push 済み、main には未取り込み）。worktree は `.claude/worktrees/todo079`。

## 変更点

- `recognizer/dice.py`
  - `read_dice` を、読みを集める `_found`（今の形の検出から）と、読みからダイスと `values` を決める `_read` に分けた。
    今までの判定の中身は変えていない。`_read` に、2 つのダイスの色の差の上限 `hue`（既定 15、今までどおり）を足した
  - `_pip_found`（新規）: 目から探す。top-hat / black-hat（まわりの大きさ 0.1・0.25 × 駒の直径）を 60〜195 の 10 段で切って目の候補を取り、
    目の対の中点（2・4・6）か片方の目（3・5）を中心に正方形を置く。正方形の中の目が面になり、`_pips`・`_pips_level` でも同じ目に読めるものを読みとする
    （切る位置ごとに 1 か所 1 つ、目の多い面を採る）。目の大きさが正方形の 2〜8%、バーの上は除く
  - `read_dice` は、今の方法で `values` が `None` のときだけ `_pip_found` で読み直し、`values` が出たときだけその結果に差し替える（色の差の上限は 25）
  - 駒の上を捨てる条件を `_on_checker` にまとめ、両方の道で使う
- `analyzer/test_dice.py`（新規）: photo-black-blue-oblique を `board.recognize` で読み、`values == [6, 2]`
- `recognizer/board.py:78` `__version__` 0.29.3 → 0.30.0
- `recognizer/accuracy_baseline.json`: photo-black-blue-oblique の dice が not read → ok（ほかの行は変わらない）
- `recognizer/README.md` のダイスの節: 手順 6. と、表の行・斜め撮影の 8 枚の結果を足した
- `TODO.md` の TODO-079: 題・背景・見込み・チェックボックスを指示どおりに書き直した
- 測る道具: `archives/agents/TODO-079/count.py`（1 枚の `_pip_found` の読みと結果、`pip_readings_<名前>.png` を書く）、`pip_readings_crop.png`

## 斜め撮影でダイスのある 8 枚（evaluate.py で 1 枚ずつ）

| サンプル | 正解 | 前 | 後 |
|---|---|---|---|
| photo-black-blue-oblique | 6-2 | not read | **ok** |
| collected-black-red-oblique | 3-1 | not read | not read（1 の目） |
| collected-brown-cream-oblique | 4-1 | not read | not read（1 の目） |
| collected-cream-black-oblique | 3-1 | not read | not read（1 の目） |
| collected-red-blue-oblique | 6-1 | not read | not read（1 の目） |
| collected-cream-red-oblique | 6-4 | not read | not read（写真が粗く、目が見えない） |
| collected-cream-red-black-oblique | 6-3 | not read | not read（同上） |
| collected-green-red-white-oblique | 4-4 | not read | not read（片方は 4 を確かと読むが、小さな白いダイスの目の光り方で、もう片方を 2 個の目と見る） |

WRONG は 0 件。

## 検証

- `uv run python recognizer/check_accuracy.py --update`（1 回だけ）: 終了コード 0、3 分 9 秒、1799/2064 points（前と同じ）。
  基準で変わったのは上の 1 行だけ（ポイント・バー・ホーム・キューブ・ほかのダイスは全サンプルで変わらない）。
  既定の並列数（CPU の数）で流したので、プロセスが多く立った（利用者から指摘あり。次から `--jobs=4`）
- `uv run pytest analyzer/test_dice.py`: 通る。`read_dice` の差し替えを止めると落ちることを確かめた（壊すと落ちる）
- `uv run ruff check` / `uv run ruff format --check`: 通る
- CI（af6a0e7）: ruff 39385133927・test 39385133788・accuracy 39385133624、どれも `gh run watch --exit-status` で終了コード 0

## 判断が要る点・残る懸念

- **色の差の上限を、目から探す道だけ 15 → 25 にした。** photo-black-blue-oblique の 6 と 2 は a・b の差が 17.7（6 の面が明るく白っぽく写る）。
  上限 15 のままでは読めない。色違いの 2 組を 1 組と見るおそれは上がるが、全サンプルで誤読は増えていない
- 時間: 今の方法で 2 つそろわないサンプルでは、目から探す分が 1 枚あたり 0.1〜1.3 秒（`_pip_found` だけで測った値）と、読みの分だけ増える
- 1 の目は目の対が無いので、この方法では見つからない（8 枚のうち 4 枚）。片方を形で、もう片方を目で見つけて合わせることはしていない
- `--debug` のダイスの画像は、目から探す結果を使ったときは、その読みの正方形を描く
- テストは 1 枚の写真の結果だけを見ている。「2 つ読めているサンプルの結果を変えない」は、`read_dice` の分岐（`values is None` のときだけ）と基準の差分で確かめた
