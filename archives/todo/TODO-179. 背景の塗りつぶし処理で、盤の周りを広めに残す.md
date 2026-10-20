# TODO-179. 背景の塗りつぶし処理で、盤の周りを広めに残す

|      | main | 担当 |
|------|------|------|
| 見込み | Sonnet 5.5 / effort medium | implementer（Opus / medium）+ reviewer（Opus / medium）→ verifier（Sonnet / medium）。塗る範囲が変わる分岐の変更なので reviewer を付ける。reviewer を先、verifier を後 |
| 実施 | Sonnet 5.5 / effort 未確認 | implementer（Opus 5.5 / medium）+ reviewer（Opus 5.5）→ verifier（Haiku 5.5） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main + 担当 | Haiku 5.5 | 未確認 | 190 | 83,678 | 227,142 | 5,684,999 | 34% |
| main + 担当 | Opus 5.5 | 未確認 | 190 | 32,348 | 168,401 | 5,656,256 | 34% |
| main + 担当 | Sonnet 5.5 | 未確認 | 192 | 37,923 | 191,778 | 5,325,800 | 32% |
| 合計 |  |  | 572 | 153,949 | 587,321 | 16,667,055 | 計 17,408,897 |

- `token-usage.py` は担当ごとに分けられず、モデル別の 3 行で出た。担当のモデルと effort は main の依頼から写したもので、記録からは確かめていない（Haiku の行は verifier と見られる）
- 範囲の終点は最初の実装のコミット（1210b67）で、レビューの指摘の直しとマージ・決着の分は入っていない

## きっかけ

読み違いの組を `samples/` に入れるときの背景の塗りつぶし処理（`recognizer/import_collected.py` の `paint`）は、四隅のちょうど外を黒くしていた。
元の写真と大きく変わり、精度の改善に役立たないことが多い（2026-10-20 ユーザーの指摘）。

## やったこと

- `recognizer/import_collected.py`: `paint` を、盤の中心（四隅の平均）から各隅までの距離を 1.1 倍にした四角（各辺の外に約 5%）の外を黒くするように変えた（`MARGIN = 0.1`）。写真の外へはみ出す分は `cv2.fillPoly` が写真の端で切る。1.1 倍の読み方はユーザーが了承した
- `analyzer/test_collected.py`: `paint` の境目と写真の端を確かめるテストを足した。取り込みのテストは、書き出した写真が `paint` の結果と画素まで同じことを確かめる形にした
- `samples/collected-*` のうち `collected/` に元の写真があった 22 組のうち 20 組を、開発機で塗り直した（`archives/agents/TODO-179/repaint.py`。`id` で対応させた）。写真の大きさと四隅の座標は変えていない
  - collected-galaxy-screen-9 は TODO-175 で塗っていない元の写真にしてあるので、そのままにした
  - collected-tan-black-side-1 は手で入れた組で、新しい幅で塗ると盤の右上の外に人の肌が出るので、そのままにした
- `recognizer/accuracy_baseline.json` を書き直し、`recognizer/README.md` の集めた写真の行を 1392 ポイント中 1196 → 1181 にした（塗り直した組が元の写真に近づいた分。読み取りのコードは変えていない）
- CLAUDE.md の「変えないもの」と `docs/raspi.md` に、塗る範囲と、周りの手や物が写りやすくなることを書いた
- 版は上げなかった（取り込みの道具で、アプリの読み取りの結果は変わらない）。ローカルの確認は要らないと判断した

## 確かめたこと

- CI の test・accuracy・ruff が通った（PR #535）
- reviewer（`archives/agents/TODO-179/reviewer-report.md`）: 指摘 3 点（`docs/raspi.md` の記述、取り込みのテストが塗ったことを確かめていない、「10%」の書き方）を直したあと、要修正なし。`add()` から `paint` を外すとテストが落ちることを確かめた
- verifier（`archives/agents/TODO-179/verifier-report.md`）: 3 組で、写真の大きさが同じ・盤の中が元のまま・1.1 倍の四角の外が黒いことを測った。blue-red-top の時計のような物、wood-side の指のような肌色は CLAUDE.md の決まりどおりそのまま公開する

## 残ること

- `docs/corner-methods.md` の「背景の塗りつぶし処理が測り方に効いている」の数値は前の塗り方で測ったもの（reviewer の検討 4。今の幅で値が変わるかは未確認）

## 分担の振り返り

- reviewer が、取り込みのテストから塗ったことの確かめが抜けたこと（`paint` を外しても通る）と、`docs/raspi.md` の古い記述を見つけた。implementer は `paint` の単体のテストを足して満足していて、呼び出し側の抜けに気づかなかった。実装と確認を分けた効果が出た
- 見込みと違ったのは verifier のモデル（Sonnet の見込みに対し Haiku）。測る対象は 3 組と少なく、Haiku で足りた
- implementer が塗り直しの途中で、手で塗ってあった組（tan-black-side-1）の人の肌に気づいて止めた。次に同じ規模なら、塗り直しの依頼に「手で入れた組・わざと塗っていない組は git log で見分けて外す」と書いておく。`check_accuracy.py --help` が全サンプルの確認として走ってしまったので、引数を知らない道具は先に docstring を読む
