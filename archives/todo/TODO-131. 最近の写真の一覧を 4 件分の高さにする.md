# TODO-131. 最近の写真の一覧を 4 件分の高さにする

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort high | main（実装）+ verifier（Haiku 5.5 / medium） |
| 実施 | Opus 5.5 / effort high | main（実装）+ verifier（Haiku 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | high | 26 | 5,894 | 9,910 | 872,013 | 74% |
| verifier | Haiku 5.5 | medium | 20 | 2,540 | 68,934 | 245,416 | 26% |
| 合計 |  |  | 46 | 8,434 | 78,844 | 1,117,429 | 計 1,204,753 |

- 集計の終点は fix のコミット（6a22984）。マージ後のローカルの確認と決着の分は入っていない

## きっかけ

最近の写真の一覧（`.history-list`）が 10 件分の高さで、写真の画面がスマホの 1 画面に収まらなかった。
ユーザーは初め 5 件分と言い、項目を立てたあとで 4 件分に直した（2026-10-18）。

## やったこと

- `analyzer/static/style.css` の `.history-list` の `max-height` を `calc(4 * 78px + 3 * 8px)`（336px）にした。残す枚数（`KEEP = 100`）は変えていない
- analyzer を 0.73.1 に上げた（`analyzer/app.py`・`analyzer/static/app.js`）。PR #386

## 確かめたこと

- verifier: 作業ツリーのコードを 8031 番で立て、412×848 のモバイルの画面で最近の写真を 5 件入れて測った。ページの scrollHeight 848 ≤ innerHeight 848、一覧の clientHeight 336 < scrollHeight 422（5 件目は一覧の中でスクロール）。スクリーンショットでも部品の欠けや重なりは無かった（`archives/agents/TODO-131/verifier-report.md`）
- ローカル（マージ後）: `/version` は 0.73.1・49bd8af、配っている `style.css` は 4 件分。live_view の窓（最近の写真は 1 件）でも 848/848 に収まった
- CI の test は通った

## 分担の振り返り

- verifier（Haiku 5.5）は、指定した値をそのまま測って合否を出した。食い違いは見つけていない
- 見込みとの食い違いは無い
- 次に CSS の 1 行だけの項目なら同じ組み方でよい。ただし 848/848 のように余裕が 0 px だったので、高さの余裕も報告に入れさせる（端末のアドレスバーの分で溢れるかを判断できるように）
