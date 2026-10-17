# TODO-117. 最近の写真の説明文を 100 件に直す

| | main | 担当 |
|---|---|---|
| 見込み | Opus 5.5 / effort high | main（実装）+ verifier（Haiku 5.5 / medium） |
| 実施 | Opus 5.5 / effort high | main（実装）+ verifier（Haiku 5.5 / medium）。TODO-109・TODO-115 と一緒に |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | high | 66 | 15,583 | 78,039 | 2,511,175 | 77% |
| reviewer | Opus 5.5 | high | 22 | 103 | 53,473 | 398,462 | 13% |
| verifier | Haiku 5.5 | medium | 20 | 5,409 | 35,781 | 270,871 | 9% |
| 合計 |  |  | 108 | 21,095 | 167,293 | 3,180,508 | 計 3,369,004 |

- TODO-109・TODO-115・TODO-117 を 1 つのブランチ（PR #338）でまとめて実施したので、表は 3 項目を合わせた量（分けられない）。reviewer は TODO-115 の分だけを見た
- reviewer・verifier は定義（`~/.claude/agents/`）のまま（opus / high、haiku / medium）

## きっかけ

写真の画面の「最近の写真」の説明が「最近の 10 枚を…」のままで、TODO-095 で 100 件まで残すようにしたのと食い違っていた（2026-10-17 ユーザーが直すと決めた）。

## やったこと

`analyzer/static/index.html` の文言を「最近の 100 枚を、この端末の中だけに残します。」に直した。README は既に 100 枚だった。analyzer 0.65.0（PR #338）。

## 確かめたこと

- verifier: `#history .note` が新しい文言、`rg -n "最近の 10 枚" analyzer` が 0 件（`archives/agents/TODO-115/verifier-report.md`）
- ローカル: マージ後の bganalyzer.service（0.65.0）が返す `/` に新しい文言がある

## 分担の振り返り

- verifier は、live_view のブラウザでこの項目の文言と TODO-115 の操作を 1 本のスクリプト（`archives/agents/TODO-115/check.py`）でまとめて測り、食い違いは無かった。reviewer はこの項目の文言は見ていない
- 見込みとの食い違いは無い
- 次に文言だけの小さな項目をやるときも、ほかの項目と同じ PR に入れ、verifier を 1 回で済ませる
