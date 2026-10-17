# TODO-101. photo5 の home の推測が外れる

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort high | main（調査・実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |
| 実施 | Opus 5.5 / effort low | main（調査・実装）+ verifier（Haiku 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | low | 42 | 9,358 | 60,452 | 1,355,570 | 89% |
| verifier | Haiku 5.5 | medium | 12 | 1,463 | 31,998 | 137,380 | 11% |
| 合計 |  |  | 54 | 10,821 | 92,450 | 1,492,950 | 計 1,596,275 |

- reviewer は入れなかった。変えたのは正解のデータと、テストの例外を 1 つ外すことだけで、コードの分岐は変わらないため
- 集計は `--since '2026-10-18 06:55:00'`（立ててから着手まで空いた）

## きっかけ

`samples/photo5.jpg` は駒を 24/24 正しく読むが、home の推測が外れていた（`evaluate.py` の margin +16.5、正解は left）。TODO-077 の「残ること」。

## やったこと

- 正解の盤面と、鏡に映した盤面の対数尤度をポイントごとに比べた。home left では white の 6・13 が空で 7・9・12 に 2 つずつ、
  black はバーポイントに 5 つと、まず出ない形（-54.1）。home right なら両者とも 6・8・13 に駒がある序盤のふつうの形（-37.5）
- 写真を見せ、2026-10-18 ユーザーが正解を home right に直すと決めた。推測のやり方（`home_prior.py`）は直さない
- `samples/photo5.truth.json` の home を right にし、points を `home_prior.mirror` で映した値にした（note に経緯を追記）
- `recognizer/accuracy_baseline.json` の photo5 の home を true にした
- `analyzer/test_api.py` の `test_home_side_is_guessed_from_the_checkers` から photo5 の例外を外した

## 確かめたこと

verifier（`archives/agents/TODO-101/verifier-report.md`）:

- 新しい points が旧 points の鏡と一致し、駒は white 15・black 15。四隅など home と points 以外は変わっていない
- `evaluate.py samples/photo5.truth.json` で 24/24、home guess ok（+16.5）。基準の行と一致
- `test_api.py -k home_side_is_guessed` と `test_side.py` が通る

## 分担の振り返り

- verifier は食い違いを見つけなかった。指示に無い note の追記を拾って報告した（意図した変更なので残した）
- 見込みより軽く済んだのは、調べた結果がコードの直しでなく正解の直しになったため。reviewer は外した
- 次に正解のデータだけを直す項目なら、main の調査と verifier（Haiku 5.5）1 人で足りる
