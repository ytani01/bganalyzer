# TODO-109. 「うまく読み取るコツ」に写真の向きを書く

| | main | 担当 |
|---|---|---|
| 見込み | Opus 5.5 / effort high | main（文案・実装）+ verifier（Haiku 5.5 / medium） |
| 実施 | Opus 5.5 / effort high | main（実装）+ verifier（Haiku 5.5 / medium）。TODO-115・TODO-117 と一緒に |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | high | 66 | 15,583 | 78,039 | 2,511,175 | 77% |
| reviewer | Opus 5.5 | high | 22 | 103 | 53,473 | 398,462 | 13% |
| verifier | Haiku 5.5 | medium | 20 | 5,409 | 35,781 | 270,871 | 9% |
| 合計 |  |  | 108 | 21,095 | 167,293 | 3,180,508 | 計 3,369,004 |

- TODO-109・TODO-115・TODO-117 を 1 つのブランチ（PR #338）でまとめて実施したので、表は 3 項目を合わせた量（分けられない）。reviewer は TODO-115 の分だけを見た
- reviewer・verifier は定義（`~/.claude/agents/`）のまま（opus / high、haiku / medium）

## きっかけ

四隅の推定は、盤のバーが写真の縦になる向きを前提にしていて、盤が回っていると見つからない（TODO-104）。回っているときは四隅の画面の「左に 90°・右に 90°」で直せることを、写真の画面の「うまく読み取るコツ」に書く（2026-10-17 ユーザーが決めた）。

## やったこと

`analyzer/static/index.html` の `details.tips` に、ユーザーが決めた文言を足した:「手前の人が写真の下になる向きで撮る（バーが縦になるように）。向きが違うときは、四隅の画面で 90° 回せる」。
着手したときにユーザーから、振ったダイスは読むので「ダイスやカップは盤の外に置く」は合わないと言われ、「ダイスは、見やすい位置に置く」「カップなど、不要なものはボードの外に置く」の 2 行に替えた。analyzer 0.65.0（PR #338）。

## 確かめたこと

- verifier: `details.tips li` に 3 行が入り、古い行が無い（`archives/agents/TODO-115/verifier-report.md`）
- ローカル: マージ後の bganalyzer.service（0.65.0）が返す `/` に新しい文言がある

## 分担の振り返り

- verifier は、live_view のブラウザでこの項目の文言と TODO-115 の操作を 1 本のスクリプト（`archives/agents/TODO-115/check.py`）でまとめて測り、食い違いは無かった。reviewer はこの項目の文言は見ていない
- 見込みとの食い違いは無い
- 次に文言だけの小さな項目をやるときも、ほかの項目と同じ PR に入れ、verifier を 1 回で済ませる
