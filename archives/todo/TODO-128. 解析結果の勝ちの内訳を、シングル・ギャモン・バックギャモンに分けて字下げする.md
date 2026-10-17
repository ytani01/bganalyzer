# TODO-128. 解析結果の勝ちの内訳を、シングル・ギャモン・バックギャモンに分けて字下げする

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort medium | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |
| 実施 | Opus 5.5 / effort 記載なし | main（実装・ローカルの確認）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | 記載なし | 76 | 16,659 | 35,473 | 3,189,653 | 85% |
| reviewer | Opus 5.5 | high | 18 | 73 | 41,782 | 272,894 | 8% |
| verifier | Haiku 5.5 | medium | 16 | 1,722 | 38,067 | 217,227 | 7% |
| 合計 |  |  | 110 | 18,454 | 115,322 | 3,679,774 | 計 3,813,660 |

- reviewer は定義のモデルが opus。呼び出しでも opus を指定した（同じ）
- verifier は定義どおり haiku（Haiku 5.5）・medium
- main の effort は記録に残っていない

## きっかけ

結果の表の「うちギャモン勝ち」「うちバックギャモン勝ち」は gnubg の値そのままで、ギャモンがバックギャモンを含む。
「うち」の意味と重なりが分かりにくいと、ユーザーが重ならない 3 つに分けて字下げすることを決めた（2026-10-18）。

## やったこと

- `analyzer/static/result.js`: 「勝率」の下に、シングル勝ち（win − gammon）・ギャモン勝ち（gammon − backgammon）・バックギャモン勝ち（backgammon）を `class="sub"` の行で並べる。
  差は小数 1 桁に丸め、0 未満は 0 にする（サーバーは数字を 1 つずつ丸めるので、相手側のシングル勝ちが -0.1% になりうる。reviewer の指摘）
- `analyzer/static/style.css`: `.result td.sub` に `padding-left: 1.5em`
- `analyzer/test_pwa.py`: `test_win_table_splits_gammons`（丸めと 0 未満の場合も）
- `analyzer/README.md` の結果の画面の説明を合わせた。analyzer 0.71.0 → 0.72.0（`APP_VERSION` も）
- 読み上げの文（`p.gammon >= 25`）は変えていない

## 確かめたこと

- verifier: `analyzer/test_pwa.py` が 26 passed。丸めを外す・0 未満の扱いを外す・シングル勝ちを `q.win` にする、のどれでも新しいテストが落ちる。node の `R.html` で行の並びと和が勝率に合う（`archives/agents/TODO-128/verifier-report.md`）
- CI の pytest が通ってから PR #377 をマージ
- ローカル（analyzer 0.72.0、live_view の窓）: 勝率 50% の下に 白 36.8 / 12.6 / 0.6・黒 36.4 / 13 / 0.6 が字下げ 21px で出て、足すと 50%

## 分担の振り返り

- reviewer: テストが丸めを外しても落ちないこと、README の表の説明が古いこと、相手側の差が -0.1% になりうることを見つけた。3 つとも直した
- verifier: 4 つの確認はすべて合った。0 未満を 0 にする扱いが TODO の本文に無いことを報告し、本文に書き足した
- 見込みとの食い違いは無い。次に同じ規模（表示 1 か所と CSS、テスト 1 つ）なら同じ組み方でよい。verifier の確認のうち node で表を組む分は、テストと重なっていたので外せる
