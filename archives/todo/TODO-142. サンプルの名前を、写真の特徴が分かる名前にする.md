# TODO-142. サンプルの名前を、写真の特徴が分かる名前にする

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort high | main（名前の案・実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |
| 実施 | Opus 5.5 / effort high | main（名前の案・実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | high | 304 | 80,798 | 247,018 | 19,009,466 | 80% |
| reviewer | Opus 5.5 | high | 140 | 5,895 | 222,404 | 2,912,338 | 13% |
| verifier | Haiku 5.5 | medium | 84 | 6,318 | 136,513 | 1,474,847 | 7% |
| 合計 |  |  | 528 | 93,011 | 605,935 | 23,396,651 | 計 24,096,125 |

- 集計の範囲は 8edf1f7 まで。2026-10-19 のローカルの確認（TODO-147 の取り込みで一緒に確かめた）の分は入っていない

## きっかけ

2026-10-19 ユーザーの依頼。`samples/` の名前（`collected-2aunci` など）では、どんな写真か分からない。

## やったこと

- 名前の決まりを `<出どころ>-<盤の特徴>-<撮り方>[-番号]` にし（ユーザーが決めた）、collected-*・photo2〜6・screen1・2・synth-* を改名した。tv-vegas-open・commons-*・external はそのまま
- 写真・`*.truth.json` の `image`・`accuracy_baseline.json`・テスト・README・docs の参照を新しい名前にした（280b3e2）
- `recognizer/import_collected.py` で、取り込む組に `claude -p` で名前を付けさせる（使えないときは今までの乱数の名前）。取り込み済みかは名前でなく `*.truth.json` の `id` で見分ける
- レビューの指摘で、CREDITS.md の壊れた範囲の書き方、`id` で見分けることのテスト、CLAUDE.md の「外へ送る例外」の一覧を直した（8edf1f7）

## 確かめたこと

- `analyzer/test_collected.py` が通る。精度は CI の accuracy に任せた
- ローカル: 2026-10-19 の自動取り込みの PR #435 で、足した 10 組が collected-yellow-red-oblique・collected-galaxy-screen-8 などの名前になった

## 分担の振り返り

- reviewer は要修正を 3 つ見つけた（機械的な置換で壊れた範囲の書き方、`id` での見分けを守るテストが無いこと、CLAUDE.md との食い違い）。どれも verifier の静的な確認では拾えない種類だった
- verifier は参照の漏れを `rg` で確かめ、食い違いは無かった
- 見込みと実施は同じ。次に同じ規模の改名をやるなら、置換のあとに旧名を含む行の文として読めるかを reviewer に見させる指示を最初から書く
