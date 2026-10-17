# TODO-103. 「マネーゲーム」を「アンリミテッド」に代える

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort high | main（実装）+ verifier（Haiku 5.5 / medium） |
| 実施 | Opus 5.5 / effort high | main（実装）+ verifier（Haiku 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | high | 38 | 7,314 | 13,020 | 2,531,702 | 96% |
| verifier | Haiku 5.5 | medium | 8 | 1,571 | 32,935 | 81,764 | 4% |
| 合計 |  |  | 46 | 8,885 | 45,955 | 2,613,466 | 計 2,668,352 |

- verifier は定義（`~/.claude/agents/verifier.md`）のモデル・effort のまま（haiku / medium）

## きっかけ

ユーザーが、「マネーゲーム」という語をすべて「アンリミテッド」に代えると決めた（2026-10-17）。

## やったこと

- `rg -n "マネーゲーム" -g '!archives/**'` で出た箇所を置き換えた: `analyzer/static/app.js`（ゲームの選択肢）、`analyzer/static/result.js`（キューブ判断の注記）、
  `analyzer/test_pwa.py`、`analyzer/README.md`、`docs/HANDOVER.md`、TODO.md の TODO-025 の節。TODO-103 の節の説明と `archives/` は変えていない
- analyzer 0.62.0 → 0.62.1（`APP_VERSION` も）

## 確かめたこと

- verifier: 残りは TODO-103 の節だけ、置き換え以外の変更なし、`test_match_in_the_result_words` が通る（`archives/agents/TODO-103/verifier-report.md`）
- PR #311 の GitHub Actions の `test` が通った
- ローカル: マージ後の `/version` が analyzer 0.62.1。Chromium で開いた盤面の画面の「ゲーム」の選択肢の先頭が「アンリミテッド」。
  結果の注記は解析しないと出ないので、配信される `result.js` に「アンリミテッド」があることで確かめた

## 分担の振り返り

- verifier は食い違いを見つけなかった。画面の表示は見ていないと自分で書いてきた（ローカルの確認で main が見た）
- 見込みと食い違わなかった
- 文言の置き換えだけの項目では、`rg` が 0 件になることとテスト 1 件で足りる。次も同じ組み方で、verifier の手順は 3 つまでに絞る
