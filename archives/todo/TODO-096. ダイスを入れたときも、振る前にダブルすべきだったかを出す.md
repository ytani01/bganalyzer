# TODO-096. ダイスを入れたときも、振る前にダブルすべきだったかを出す

| | main | 担当 |
|---|---|---|
| 見込み | Opus 5.5 / effort medium | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |
| 実施 | Opus 5.5 / effort medium | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | medium | 106 | 21,499 | 93,425 | 4,922,663 | 75% |
| reviewer | Opus 5.5 | high | 36 | 188 | 70,450 | 879,216 | 14% |
| verifier | Haiku 5.5 | medium | 36 | 176 | 57,832 | 681,260 | 11% |
| 合計 |  |  | 178 | 21,863 | 221,707 | 6,483,139 | 計 6,726,887 |

- TODO-095 の分も含む（同じ PR で一緒に進めた）。`--since '2026-10-17 07:10:05'` から決着の直前まで
- main の分には、途中のユーザーの質問（gnubg の「(25.6%)」の意味。gnubg のソースを取ってきて `getPercent()` を読んだ）も入っている
- verifier は呼び出しで `model: haiku` を指定（定義と同じ）。ツールの記録では reviewer・verifier とも claude-opus-5-5 に数えられているが、そのまま写した
- サブエージェントの分は少なめに出る（todo-workflow skill）

## きっかけ

ユーザーの依頼（2026-10-17）。ダイスを入れると最善手だけで、振る前にダブルすべきだったかが分からなかった。
着手後に「ダブルすべきだった場合だけ出す」と決まった（ダブルしない・してもしなくてもよい・ギャモン狙いのときは出さない）。

## やったこと

- `analyzer/engine.py`: `evaluate` が `(確率, キューブの判断, 最善手)` を返すようにし、キューブとダイスを両方求められるようにした
- `analyzer/analysis.py`: ダイスがあってもキューブが中央か手番の側なら振る前のキューブの判断を求め、`double` のときだけ `cube` に入れる（`rolled: true`）。概要の文は「振る前、白はダブルすべき、黒はパス」
- `analyzer/static/result.js`: 見出し「キューブ（振る前）」と「白の人は振る前に ダブルすべきだった」を最善手の前に出す。読み上げも最善手より先に「振る前に白の人はダブルすべきでした。ダブルされたら黒の人はパスです。」（reviewer の指摘を受けてユーザーが決めた）
- `analyzer/models.py` のコメント、`analyzer/README.md`（画面・読み上げ・API の `cube` と `rolled`）
- `analyzer/test_api.py`・`analyzer/test_pwa.py`: ダブルすべき局面で出る・初期局面と相手が持つときは出ない・画面と読み上げの順。screen2 は中央のキューブだとダブルすべき局面なので、その確かめを書き換えた
- analyzer 0.59.0

## 確かめたこと

- reviewer（`archives/agents/TODO-096/reviewer-report.md`）: 要修正 0 件。doubled・ダイスなし・相手が持つ・クロフォードの分岐は仕様どおり。古いコメントと文書、読み上げの順を指摘 → 直した
- verifier（`archives/agents/TODO-096/verifier-report.md`）: ダブルすべき局面 + ダイス 3-1 で `rolled: true`・最善手あり、相手が持つと `cube` なし。画面と読み上げの順も一致
- GitHub Actions の test が通ってからマージした（PR #293）
- ローカル: 0.59.0 のサービスで、同じ局面（`4O4GAHB3AwAAAA`、ダイス 3-1）で「キューブ（振る前）」が最善手より前に出て、読み上げが「振る前に白の人は…」で始まる。キューブを黒が持つと出ない

## 分担の振り返り

- reviewer は差分の外の古いコメント（`models.py`）と README の例、読み上げの順を見つけた。分岐の誤りは無かった。verifier は食い違いを見つけなかった
- 見込みどおり。ただし仕様が途中で 1 回変わった（ダブルすべきときだけ）ので、reviewer を起こす前に変わったのは良かった
- 次も、挙動が変わる小さな項目は main 実装 → reviewer（Opus）→ 直す → verifier（Haiku）の順で組む。reviewer の指摘が順番のような仕様の穴なら、verifier の前に利用者へ聞く
