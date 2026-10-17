# TODO-129. 解析結果の画面で、勝率の棒グラフの上の概要の文を出さない

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort medium | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |
| 実施 | Opus 5.5 / effort 記載なし | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | 記載なし | 88 | 12,921 | 72,121 | 3,202,642 | 85% |
| reviewer | Opus 5.5 | high | 22 | 1,542 | 42,237 | 353,222 | 10% |
| verifier | Haiku 5.5 | medium | 14 | 1,424 | 31,202 | 159,250 | 5% |
| 合計 |  |  | 124 | 15,887 | 145,560 | 3,715,114 | 計 3,876,685 |

- reviewer・verifier は定義（`~/.claude/agents/`）のモデル・effort と同じ値を Agent ツールでも渡した
- main の effort はセッションの設定で、記録に残っていない
- 集計の終点は決着のコミットの前（現在時刻まで）

## きっかけ

結果の画面の一番上の 1 行（`result.js` の `<p class="summary">`、サーバーの `summary_ja`）は、下の棒グラフ・表・キューブの判断と同じことを言っている（2026-10-18 ユーザー）。

決めたこと（2026-10-18 ユーザー）: 画面からだけ消す。API の `summary`（`tools/check_pi.py` が使う）と読み上げの文は変えない。終局した局面の「白の勝ちで終局しています。」も消す。

## やったこと

- `analyzer/static/result.js`: `html` が概要の文を出さないようにした（一番上が勝率の棒グラフになる）
- `analyzer/static/style.css`: 使われなくなった `.result .summary` を消した
- `analyzer/test_pwa.py`: 棒グラフが先頭にあり、概要の文が出ないことを確かめるようにした
- `analyzer/README.md`: 結果の画面の説明を合わせた
- analyzer 0.72.0 → 0.73.0（`APP_VERSION` も）。PR #379

## 確かめたこと

- verifier: `analyzer/test_pwa.py` が通る。概要の文を戻すと `test_result_html` が落ちる。版は両方 0.73.0
- reviewer: 要修正なし。README の「下の注記」が何か分からない、の指摘で文を直した
- ローカル（マージ後、analyzer 0.73.0・133ea70）: Playwright でサンプルを読んで解析し、`#outcome` の結果の最初の要素が `<div class="winbar">`、`.summary` は無い

## 残ること

- 終局の局面では、盤面図の下が「gnubg 2手読み・勝率とエクイティはキューブなし。Position ID: …」の注記だけになる。勝率もエクイティも出ないので、注記の前半は意味をなさない（reviewer の指摘。前からある文言で、ユーザーの決めたとおり消した結果）

## 分担の振り返り

- reviewer は終局の画面に注記しか残らないこと（node で実測）と、README の言葉足らずを見つけた。verifier は食い違いを見つけなかった
- 見込みどおりの編成で、食い違いは無い
- 次に同じ規模（1 行を消すだけの画面の変更）なら、reviewer の effort を medium に下げてよい。verifier の依頼は今回のように 3 点に絞る
