# TODO-118. 読み上げで「〜方が」を「かたが」と読む

| | main | 担当 |
|---|---|---|
| 見込み | Opus 5.5 / effort high | main（実装）+ verifier（Haiku 5.5 / medium） |
| 実施 | Opus 5.5 / effort high | main（実装）+ verifier（Haiku 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | high | 4 | 1,165 | 2,086 | 233,302 | 100% |
| 合計 |  |  | 4 | 1,165 | 2,086 | 233,302 | 計 236,557 |

- `token-usage.py` は修正のコミット（ac8315e）までで切るので、そのあとに動いた verifier（Haiku 5.5 / medium、定義のまま）と決着の作業は入っていない

## きっかけ

読み上げの「ダブルせず、ギャモンを狙う方がよいです」「まだダブルしない方がよいです」を、Google の読み上げが「かたが」と読んだ（2026-10-17 ユーザーの報告）。

## やったこと

読み上げの文（`analyzer/static/result.js` の `speechText`）の 2 か所を「ほうが」に直し、`analyzer/test_pwa.py` の期待値も合わせた。結果の画面の表は「方が」のまま（ユーザーが決めた）。analyzer 0.65.1（PR #341）。

## 確かめたこと

- verifier: `test_pwa.py` が通る。「しない方が」に戻すと落ちる。`speechText` に「方が」が残っていない（`archives/agents/TODO-118/verifier-report.md`）
- スマホ: ユーザーが実機で「ほうが」と読むことを確かめた（2026-10-17）

## 分担の振り返り

- verifier は食い違いを見つけなかった。テストが壊すと落ちることを確かめた
- 見込みとの食い違いは無い
- 次に読み上げの文言だけを直すときも、verifier（Haiku）に test_pwa.py と壊して落ちるかだけを頼めば足りる
