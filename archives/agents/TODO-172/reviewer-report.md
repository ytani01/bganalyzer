# TODO-172 reviewer の報告

対象: `git diff origin/main...HEAD`（PR #513）。要修正 0 件、検討 1 件、好みの範囲 1 件。

## 検討

### `recognizer/corners.py:327-336` 「先端の間が平ら」の式が長い

`e[0] * e[0] + e[1] * e[1] + e[2] * e[2] < 4 * PLAIN_DE * PLAIN_DE` を `float(( ... ).sum())` で包み、
ruff format の折り返しで 10 行になっている。`(e * e).sum(0) < 4 * PLAIN_DE * PLAIN_DE` でも整数のままで値は同じ
（チャンネルが 0 軸に来たので `sum(0)`）。速さの差は未確認。直前の `d4 = sum(... for c in range(3))` も同じ形で、
こちらはチャンネルごとに `take` する意図があるので残してよい。

## 好みの範囲

### `recognizer/corners.py:206` コメントが読み取りにくい

「(block, line) of the upright line through (x, y), and of the slanted one: less the shift」は、
`at` が「傾き 0 の線の通し番号で、傾いた線はそこから shift を引いたもの」という意味だと読むまでに時間がかかる。

## 問題が無かった観点

- **どんな入力でも前と同じか:** コードを追って同じと判断し、ランダムな入力でも確かめた。古い `corners.py`（`git show origin/main:`）と
  1 つのプロセスで比べ、`_structure` は RW×RH・その半分の 2 つの大きさで、乱数・単色（0/128/255）・2 値の 38 枚ずつ（計 76 件）、
  `_Upright.cum` は形 4 種（1×1・37×5 を含む）× 辺の密度 3 種 × slopes/reach 3 組（負の傾き・reach 1.0 を含む）の計 36 件。
  **112 件すべて一致（dtype も同じ）**。
  - float の順序: `v` は元も今も、.25 の倍数を足した正確な値で、形 (24, n)・C 連続も同じなので、後の `v.sum(1)` などの足し算の順も変わらない
  - 中央値: 2 倍した値の真ん中 2 つは偶数どうしで、`(lo + hi) // 2` は切り捨てにならない。奇数個なら lo == hi
  - オーバーフロー: 差 ≤ 510、2 乗の和 ≤ 780300 で int32 に収まる。`cum` は 1 列あたり高々 h で、cumsum は int64 で足してから int32 に書く（元と同じ）
  - 同点の並び: argmax・sort に変更なし。`np.partition` は値だけを使う
  - 空の配列: `_Upright` で辺の画素が 0 個でも同じ（試した）。`_structure` の中央値の範囲が空になると今は例外になる（元は NaN）が、
    `_TEMPLATES` が 2 つの大きさに限っていて空にはならない（実装者の報告どおり）
  - `_shift(rows, k)[ys]`: `_shift` は要素ごとの式で、`ys` は `[0, h)` の中
- **版:** 0.28.0 → 0.28.1（patch）で CLAUDE.md どおり。README の「0.28.0」は結果の記録なので直さなくてよい
- **範囲:** 指示外の変更なし。docstring の位置の修正は小さく妥当
- **テスト:** 出力が変わらない書き換えで、CI の accuracy と test_side.py で足りる
- **文書との整合:** 説明している文書に古くなった所なし
- 作り込みすぎ: なし（`archives/agents/TODO-172/` の道具 2 本と JSON 2 つは記録として残すもので、アプリには入らない）
