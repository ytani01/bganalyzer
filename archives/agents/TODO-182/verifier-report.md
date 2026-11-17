# TODO-182 verifier-report

## 1. evaluate.py（作業ツリーの truth.json、bottom_colour=1）

`uv run python recognizer/evaluate.py samples/collected-black-red-oblique-3.truth.json`（終了コード 0）

```
collected-black-red-oblique-3.truth.json: 20/24 points correct, bar ok, home guess ok (+11.4), dice ok (read None, truth None), cube ok (read None, truth centre)
   point  1: truth -2  got -3
   point 12: truth -5  got -4
   point 16: truth +0  got -3
   point 17: truth -3  got -1
```

- points 20/24、bar ok、home guess ok、dice ok、cube ok。依頼の期待と一致。
- 基準の行（`accuracy_baseline.json`）`{"points": 20, "bar": true, "home": true, "dice": "ok", "cube": "ok"}` と一致。
- points の食い違い 4 点（1・12・16・17）は基準の 20 に含まれる既知の誤読。今回の対象外。

## 2. 壊すと失敗するか

作業ツリーは変更せず、一時ディレクトリ（`/tmp/claude-649/-home-ytani-work-bganalyzer/54baf3fd-afc4-46b1-8627-c483a046ca20/scratchpad/v182/`）に jpg と truth.json をコピーし、コピーの `bottom_colour` だけを 1 → 0 にして同じ evaluate.py を実行した。

```
collected-black-red-oblique-3.truth.json: 20/24 points correct, bar ok, home guess wrong (-16.8), dice ok (read None, truth None), cube ok (read None, truth centre)
```

- home guess が ok → wrong（+11.4 → -16.8）に変わった。bottom_colour=1 の修正は home の判定に効いている。points・bar・dice・cube は変わらない。
- 作業ツリーに戻す操作は不要だった。実行後の `git status` / `git diff --stat` は依頼時と同じ（M: TODO.md, recognizer/accuracy_baseline.json, samples/collected-black-red-oblique-3.truth.json、?? archives/agents/TODO-182/ の 2 ファイル）。

## 3. 変更ファイル

- `recognizer/accuracy_baseline.json`: 当該組の `home` を false → true、1 行だけ。
- `samples/collected-black-red-oblique-3.truth.json`: `bottom_colour` 0 → 1 と note の追記（依頼文のとおり対象外）。
- `TODO.md`: 変更あり（依頼文のとおり対象外）。確認していない。

## 確かめていないこと

- 全サンプル・check_accuracy.py は流していない（依頼どおり。CI の accuracy に任せる）。
- 「写真の手前の駒が明るい駒」かどうか自体は、画像を見て確かめていない（reviewer の範囲）。
