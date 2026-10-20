# TODO-079 レビュー指摘の修正（実装の引き継ぎ）

## 変更点

- `recognizer/dice.py:332-338`: 目から探す道（`_pip_found`）は、前の方法で盤の上（バー以外）の確かなダイスが 2 つ未満のときだけ使う。
  2 つ以上見つかって色などで読まなかったとき（2 人分のダイスが盤に出ている）は目から探さない（指摘 1）
- `recognizer/README.md:368`: 手順 6. の条件を上に合わせた
- `recognizer/README.md:371`、`archives/agents/TODO-079/implement-report.md`: 切る位置を「60〜195 の 10 段」に直した（指摘 2）
- `archives/agents/TODO-079/probe_pip_calls.py`（新規）: evaluate.py を 1 枚ずつ流し、`_pip_found` が呼ばれた回数を出す
- バージョンは 0.30.0 のまま。基準（`accuracy_baseline.json`）は書き直していない

## 確認

| コマンド | 結果 |
|---|---|
| `uv run python archives/agents/TODO-079/probe_pip_calls.py samples/commons-lg-cube-dice.truth.json` | dice ok（read None, truth None）、`_pip_found` の呼び出し **0 回**。点 22/24 は前と同じ |
| 同 `samples/photo-black-blue-oblique.truth.json` | dice ok（read [6, 2]）、`_pip_found` 1 回。点 23/24 は前と同じ |
| `uv run pytest analyzer/test_dice.py` | 1 passed、終了コード 0 |
| `uv run ruff check` / `uv run ruff format --check` | 通る、終了コード 0 |

基準を書き直さなかった理由: 前のコミットで目から探す道の結果に差し替わったのは photo-black-blue-oblique だけ（基準の差分がその 1 行）。
今回の条件はそれを狭めるだけで、その 1 枚は前の方法で確かなダイスが 2 つ未満なので変わらない。全件は CI の accuracy に任せた。

## CI

3bcba0d に対して、test 39387162560・accuracy 39387162586・ruff 39387163933。test と accuracy は `gh run watch --exit-status` で終了コード 0、ruff は success（3 つとも success）。
CI の結果を足したこのコミットは文書だけなので、run は作られない。

## 残る懸念（直していない。管理者の指示どおり）

- 検討 3: 色の差の上限 25 は photo-black-blue-oblique の 17.7 だけに合わせた値。指摘 1 の修正で、目から探す道は「2 つ見つからない」ときだけになり、2 組を 1 組と見る筋は小さくなった
- 検討 4: 目から探す道の読みは 4 通り × 10 段で集まるのに、「確か」のしきい値 `MIN_READINGS = 4` が前の方法と同じ。偶然の模様が確かになりうる。実害は未確認
- 前の方法で確かなダイスが 1 つだけ、もう 1 つが盤に出ていない写真では、目から探す道が別の場所に 2 つ目を作ると読み違えうる（今のサンプルでは起きていない）
