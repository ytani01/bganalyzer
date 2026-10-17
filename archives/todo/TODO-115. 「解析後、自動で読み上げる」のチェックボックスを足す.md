# TODO-115. 「解析後、自動で読み上げる」のチェックボックスを足す

| | main | 担当 |
|---|---|---|
| 見込み | Opus 5.5 / effort high | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |
| 実施 | Opus 5.5 / effort high | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium）。TODO-109・TODO-117 と一緒に |

| 担当 |
|---|---|---|
| 見込み | Opus 5.5 / effort high | main（実装）+ verifier（Haiku 5.5 / medium） |
| 実施 | Opus 5.5 / effort high | main（実装）+ verifier（Haiku 5.5 / medium）。TODO-109・TODO-115 と一緒に |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | high | 66 | 15,583 | 78,039 | 2,511,175 | 77% |
| reviewer | Opus 5.5 | high | 22 | 103 | 53,473 | 398,462 | 13% |
| verifier | Haiku 5.5 | medium | 20 | 5,409 | 35,781 | 270,871 | 9% |
| 合計 |  |  | 108 | 21,095 | 167,293 | 3,180,508 | 計 3,369,004 |

- TODO-109・TODO-115・TODO-117 を 1 つのブランチ（PR #338）でまとめて実施したので、表は 3 項目を合わせた量（分けられない）。reviewer はこの項目の分だけを見た。決着の作業の分は入っていない
- reviewer・verifier は定義（`~/.claude/agents/`）のまま（opus / high、haiku / medium）

## きっかけ

解析が済んだら、「読み上げ」を押さなくても読み上げてほしい（2026-10-17 ユーザーが決めた）。既定はオフで、選んだほうを端末に覚える。

## やったこと

- 盤面の画面の「解析する」の上に「解析後、自動で読み上げる」を置いた（`analyzer/static/index.html`・`app.js`）。localStorage の `autoSpeak` に覚える
- スマホのブラウザは押した直後でないと音を鳴らさないので、読み上げを 1 つの `Audio` の使い回しに変え、「解析する」を押したときにその `Audio` で無音を鳴らし、空の `SpeechSynthesisUtterance` も入れておく
- reviewer の指摘を受けて、結果の画面を離れたら読み上げを止めるようにした（前は「止める」ボタンが隠れたまま読み続けた。手で押す読み上げでも同じだった）
- `analyzer/README.md` に説明を足した。analyzer 0.65.0（PR #338）

## 確かめたこと

- reviewer: 要修正 0 件（`archives/agents/TODO-115/reviewer-report.md`）
- verifier: live_view のブラウザで、オフでは読まない・オンで読み始める・戻ると止まる・開き直してもオンが残る（`archives/agents/TODO-115/verifier-report.md`）
- スマホ: ユーザーが実機で確かめた（2026-10-17）

## 分担の振り返り

- reviewer は、結果の画面を離れても読み続ける点と、iOS で空の発話が許可に数えられるか分からない点を見つけた。前者はこの項目で直し、後者はスマホの確認に回した。verifier は食い違いを見つけなかった
- 見込みとの食い違いは無い
- 次に同じ規模の項目をやるときも、reviewer を先、verifier を後にし、文言だけの項目は同じ PR の verifier にまとめて測らせる
