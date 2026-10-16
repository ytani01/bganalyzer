# TODO-092. 盤面を直す画面に最善手の矢印を出さず、盤に手番の進み方を出す

| | main | 担当 |
|---|---|---|
| 見込み | Opus 5.5 / effort medium | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |
| 実施 | Opus 5.5 / effort medium | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | medium | 76 | 26,039 | 49,122 | 4,240,063 | 83% |
| verifier | Haiku 5.5 | medium | 28 | 4,803 | 49,247 | 467,467 | 10% |
| reviewer | Opus 5.5 | high | 18 | 1,892 | 53,336 | 322,785 | 7% |
| 合計 |  |  | 122 | 32,734 | 151,705 | 5,030,315 | 計 5,214,876 |

- reviewer・verifier とも定義（`~/.claude/agents/`）のモデルと effort のまま
- 集計の範囲には、同じ時間に進めた TODO-090 の案の画面づくりの分も main に入っている

## きっかけ

ユーザーの依頼（2026-10-17）。解析のあと、盤面を直す画面の盤にも結果の画面と同じ最善手の矢印が出ていて要らない。
あとから、手番と進む向きが分かるように、盤に手番の側の進み方を U 字形の矢印で出したいという依頼を足した。

## やったこと

- `analyzer/static/app.js`: 盤面を直す画面の盤（`#board-svg`）には最善手を渡さない。結果の画面の盤（`#result-svg`）には今までどおり出す
- `analyzer/static/board-view.js` の `drawWay`: 手番の側の進み方を U 字形の矢印で描く（写真の盤では描かない）。
  見た目は案の画面を 3 回見せて決めた。盤の真ん中に手番の駒の色で半透明に、駒の上・ダイスの下に重ね、両端は盤の端から 1 列半ほど内側
- `analyzer/README.md` に U 字形の矢印と、最善手の矢印が結果の画面だけに出ることを書いた（reviewer の指摘）
- analyzer を 0.55.0 に上げた

## 確かめたこと

- reviewer: home が left/right × 手番が white/black の 4 通りで、矢印の始点・曲がる側・矢じり（arc の sweep を含む）が駒の進む順に合っている。直す画面の他の働きへの影響なし（[報告](../agents/TODO-092/reviewer-report.md)）
- verifier: ローカルホストで、解析のあと `#result-svg` に最善手の矢印があり `#board-svg` には無いこと、手番を切り替えると U 字形の矢印の path が変わることを確かめた（[報告](../agents/TODO-092/verifier-report.md)、スクリプトは同じ所）
- CI の test は通った

## 分担の振り返り

- reviewer は向きの誤りを見つけなかったが、README の書き漏れと、`!photo` の判定が次の行と重なっていることを見つけた（どちらも直した）
- verifier は数値で 3 点を確かめ、結果の画面を撮った。画面の上下に固定したボタンが重なって見えると報告したが、全体を撮ったせいで、今回の変更とは関係なかった
- 見込みどおり。main の分が大きいのは、見た目を決めるやり取り（案の画面 3 回）と、TODO-090 を同じ時間に進めた分が入っているため
- 次に同じ規模（描画の追加 1 つと渡す値の変更 1 つ）なら、同じ組み方でよい。verifier の撮影は、要素だけを撮るよう依頼に書く
