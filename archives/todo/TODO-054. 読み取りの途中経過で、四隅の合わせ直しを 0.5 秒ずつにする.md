# TODO-054. 読み取りの途中経過で、四隅の合わせ直しを 0.5 秒ずつにする

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort medium | main（実装）+ verifier（Haiku 5.5 / medium。Pi のヘッドレスの Chromium で、合わせ直しが 0.5 秒ずつ出るか測る） |
| 実施 | Opus 5.5 / effort medium | main（実装）+ verifier（Haiku 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | medium | 20 | 4,044 | 12,418 | 740,756 | 94% |
| verifier | Haiku 5.5 | medium | - | - | - | - | 6%（計 47,970） |
| 合計 |  |  |  |  |  |  | 計 805,208 |

- verifier は定義のモデルが haiku。呼び出しで haiku を指定した（同じ）
- verifier は `token-usage.py` の範囲（終点のコミット）のあとに動いたので集計に入らない。完了の通知にあった合計だけを書いた
- main の分は TODO-054 として立てた件（`corners.py` を速くする）の調べを含む

## きっかけ

最初は「四隅を決めるパフォーマンスを改善する」（`corners.py` を速くする）として立てた。Pi で測ると `corners.py` は 1 枚 1.0〜1.7 秒。
ユーザーがスマホで見ていた 10 秒以上の大半は、途中経過を段階ごとに 1 秒ずつ見せている時間（TODO-049、`scan.js` の `STAGE_MS`）だったので、
ユーザーの指示（2026-10-15）で、読み取りの四隅の合わせ直し（4 回）だけを 0.5 秒にする項目に書き直した。

## やったこと

- `analyzer/static/scan.js` の `STAGE_MS.fit` を 1000 から 500 に
- analyzer 0.38.1（`analyzer/app.py`、`analyzer/static/app.js` の `APP_VERSION`）、`analyzer/static/sw.js` の `CACHE` を v45 に

## 確かめたこと

verifier が Pi のヘッドレスの Chromium で photo2 を読み取り、段階の表示時間を測った（[報告](../agents/TODO-054/verifier-report.md)）。
応答をまとめて届けた場合で fit 500 / 500 / 500 / 517 ms、tips・checkers・counts・dice は 1000〜1017 ms。pytest は 63 passed / 11 skipped。

## 残ること

- ふだんの使い方（段階が届くたびに見せる）では、fit の 2〜4 回目はサーバーの計算を待つので 0.5 秒より長く出た（verifier の 1 回目で 850〜1767 ms）。
  合わせ直しの待ち時間をさらに縮めるなら、`board.py` の合わせ直しの計算を速くする必要がある

## 分担の振り返り

- verifier は表示時間を測り、ふだんの使い方では fit の 2〜4 回目がサーバー待ちになることを見つけた。main はこれに気づいていなかった
- 見込みどおりの編成。verifier は測り方を 2 回組み直して読み取りを 3 回走らせた
- 次に `STAGE_MS` だけを変えるときは、依頼に「応答をまとめて届けて STAGE_MS どおりの時間を測る」と「ふだんの応答でも 1 回測る」の 2 つを最初から書く。測り直しの分が減る
