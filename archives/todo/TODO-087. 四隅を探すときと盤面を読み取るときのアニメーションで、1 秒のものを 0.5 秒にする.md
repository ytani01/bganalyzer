# TODO-087. 四隅を探すときと盤面を読み取るときのアニメーションで、1 秒のものを 0.5 秒にする

| | main | 担当 |
|---|---|---|
| 見込み | Opus 5.5 / effort medium | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |
| 実施 | Opus 5.5 / effort medium | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | medium | 110 | 21,555 | 197,531 | 7,389,324 | 40% |
| implementer | Opus 5.5 | medium | 56 | 270 | 454,462 | 5,196,323 | 30% |
| reviewer | Opus 5.5 | high | 100 | 5,620 | 334,175 | 3,918,704 | 23% |
| verifier | Haiku 5.5 / Sonnet 5.5 | medium | 62 | 10,724 | 128,016 | 1,264,396 | 7% |
| 合計 |  |  | 328 | 38,169 | 1,114,184 | 17,768,747 | 計 18,921,428 |

- TODO-086 と同じ会話で並行して進めたので、`token-usage.py` は時間で切った両方の分を数えている。implementer は TODO-086 の担当だけで、reviewer・verifier の行にも TODO-086 の分が入る。この項目だけの分はずっと小さい
- verifier の行は、この項目の Haiku 5.5 と TODO-086 の Sonnet 5.5 の合計

## きっかけ

ユーザーの依頼（2026-10-17）。四隅を決めるとき・盤面を読み取るときのアニメーションで、1 秒のものを 0.5 秒にする。

## やったこと

- `analyzer/static/scan.js` の段階ごとの時間（`STAGE_MS`）は既に全部 500ms だった。1 秒だったのは、読み取りの応答を待つ間に三角形を描く所（`frameWaiting` の `tris`）だけで、300〜1300ms → 300〜800ms にした
- レビューの指摘（三角形だけ縮めても組み上がりの終わりが 1.4 秒のまま、0.1 秒の空きができる）を受け、バーを 900〜1400ms → 800〜1300ms にした
- analyzer 0.51.1、`sw.js` の CACHE を上げた

## 確かめたこと

- verifier: `page.clock` で時間を進め、300・550・800・1300ms の絵を撮った。550ms で三角形が途中、800ms で三角形が描き終わりバーはまだ、1300ms でバーも描き終わり、応答を返すと盤面の画面に移る（`archives/agents/TODO-087/verifier-report.md`）
- ローカル: マージ後（analyzer 0.52.0）に `BG_URL=http://127.0.0.1:8000/` で `archives/agents/TODO-087/verify.py` を流し、ページのエラー無し

## 分担の振り返り

- reviewer は、三角形だけ縮めても待つ間の絵が出来上がる時刻が変わらないことを見つけた（バーの開始を詰める直しになった）。他に 1 秒前後の動きが無いことも確かめた。verifier は時間ごとの絵で動きを確かめ、食い違いは無かった
- 見込みどおりの編成で済んだ
- 次に数値を 1 つ変えるだけの項目なら、reviewer の effort は medium で足りる。verifier は `page.clock` で時刻を決めて撮る形をそのまま使う
