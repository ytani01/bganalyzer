# TODO-097. キューブの判断に、ダブルまでの遠さを数字と日本語で出す

| | main | 担当 |
|---|---|---|
| 見込み | Opus 5.5 / effort medium | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |
| 実施 | Opus 5.5 / effort medium | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| 合計 |  |  |  |  |  |  | TODO-098 に含む |

- TODO-098 と同じブランチ・同じ PR（#297）で一緒に進め、reviewer・verifier も両方を 1 回ずつ見たので、トークンは TODO-098 のファイルの表にまとめた

## きっかけ

ユーザーの質問（2026-10-17）。キューブの判断の注記「gnubg の判断: No double, take (25.6%)」の数字の意味が分からなかった。
gnubg のソース（`eval.c` の `getPercent()`）を読んで意味を確かめ、数字と分かりやすい日本語を併記することになった。

## やったこと

- `analyzer/static/result.js`: `distanceHtml` で gnubg の `proper` の括弧の数字を読み、「ダブルまでの遠さ 26%・ダブルにはまだ少し早い」と出す。言葉は四捨五入した数字で、10% 未満「一歩手前」、30% 未満「まだ少し早い」、それ以上「まだ遠い」。Too good のときは「ギャモン狙いをやめてダブルするまでの遠さ」、リダブルの局面では「リダブル」。注記は「gnubg: …」
- `analyzer/test_pwa.py`: 区切りの両側、Too good、リダブル、数字の無い判断
- `analyzer/README.md` の結果の画面の説明
- analyzer 0.60.0（TODO-098 と一緒）

## 確かめたこと

- reviewer（`archives/agents/TODO-098/reviewer-report.md`）: 9.5〜9.9% が「10%・一歩手前」になる食い違いと、リダブルでも「ダブル」と出る点 → 直した
- verifier（`archives/agents/TODO-098/verifier-report.md`）: テストが通る
- ローカル: 0.60.0 のサービスで初期局面（ダイスなし）が「ダブルまでの遠さ 23%・ダブルにはまだ少し早い」「gnubg: No double, take (23.0%)」

## 分担の振り返り

- reviewer は丸めと言葉の食い違い、リダブルの言い回しを見つけた。verifier は食い違いを見つけなかった
- 見込みどおり
- 次も、文言だけの小さな変更は TODO-098 のような挙動の変わる項目と束ねて、reviewer・verifier を 1 回ずつにする
