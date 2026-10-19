# TODO-173 verifier の報告

## 結果

- 組数: 87（`samples/*.truth.json` すべて。side を持つ組 5 組を含む。画像が無くて飛ばした組は 0）
- 出力が完全に一致した組: **87 / 87**。食い違い 0 件（実害は未確認という話ではなく、記録した出力の JSON が全部同じ）
- 時間（`board.recognize` のみ、各 1 回、開発機）: 前 502.1 秒 → 後 319.6 秒、比率 0.636（約 36% 短縮）
- 注意: 前と後は続けて流した（交互ではない）。流す間の負荷の違い（開始時の load average 約 4）は除いていないので、時間は目安。組ごとの最大は 12.23 秒 → 3.77 秒（synth-cube-photo-carved-brown-top-16）、最小の短縮は screen-app-green-far の 9.00 秒 → 6.14 秒

## 一致の見方

`record_reading.py` は `pos.to_dict()` と `info` 全体（geometry・dice・cube・layout・pitch・checker_lab など）を JSON にして記録する。
`--compare` の出力: `samples 87 / 87, differing readings: 0`。別に Python で、前後の組名の集合が同じで、`reading` が 87 組すべて `==` なことも確かめた。

## 実行したコマンド

```bash
# 前: origin/main (0d0d46c) の別の作業ツリー（scratchpad の old）を RECOGNIZER で指す
git worktree add --detach <scratchpad>/old origin/main
RECOGNIZER=<scratchpad>/old/recognizer uv run python archives/agents/TODO-173/record_reading.py <scratchpad>/old.json   # 終了コード 0
# 後: impl-173 (0fdeb36)
uv run python archives/agents/TODO-173/record_reading.py <scratchpad>/new.json                                         # 終了コード 0
uv run python archives/agents/TODO-173/record_reading.py --compare old.json new.json
git worktree remove --force <scratchpad>/old    # 片付け済み
```

`ab_time.py` は使っていない（全サンプルを 1 回ずつ流す指示のため、`record_reading.py` を前・後 1 回ずつにした）。

## 確かめていないこと

- 精度（正解との比較）、arm64、Pi での時間は測っていない（依頼の範囲外）
- 変更されたファイルの範囲は見ていない（依頼は出力の一致と時間のみ）。`git status` は作業ツリーに未コミットの変更なし
