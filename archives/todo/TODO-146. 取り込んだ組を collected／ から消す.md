# TODO-146. 取り込んだ組を collected/ から消す

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort high | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |
| 実施 | Opus 5.5 / effort high | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | high | 474 | 151,274 | 636,207 | 42,468,278 | 96% |
| reviewer | Opus 5.5 | high | 50 | 9,167 | 135,036 | 1,128,642 | 3% |
| verifier | Haiku 5.5 | medium | 24 | 1,843 | 31,339 | 292,232 | 1% |
| 合計 |  |  | 548 | 162,284 | 802,582 | 43,889,152 | 計 44,854,566 |

- 集計の範囲は 168a97f まで。立ててから終点までの間に、ほかの作業の会話も入っていて、main の分は多めに出ている
- ローカルの確認（TODO-147 の取り込みで一緒に確かめた）の分は入っていない

## きっかけ

2026-10-19 ユーザーの依頼。`samples/` に取り込んだ組が `collected/` に残り続ける。

## やったこと

- `recognizer/import_collected.py` で、PR がマージされたときだけ、取り込んだ組の写真と正解を `collected/` から消し、`import.log` に `removed from collected/` を残す（85de633）。CI が落ちて PR が開いたままのときは消さない
- 同じ写真が別の id で送り直されたときは見分けない。取り込み済みの 36 組は残す（ユーザーが決めた）
- レビューの指摘で、`gh` が失敗したときはマージしなかったと返すことのテストを足した（168a97f）

## 確かめたこと

- `analyzer/test_collected.py` が通る
- ローカル: 2026-10-19 の自動取り込み（PR #435 のマージ）のあと、10 組が `collected/` から消え、`import.log` にそう出た

## 分担の振り返り

- reviewer は、消すかどうかを決める分岐（マージの失敗、update-branch の失敗）を壊してもテストが落ちないことを、実際に壊して見つけた
- verifier はテストが通ることを確かめただけで、新しいことは見つけなかった
- 見込みと実施は同じ。次に同じ規模なら、reviewer に「分岐を壊して落ちるか」を最初から頼み、verifier はテストの実行だけの短い依頼にする
