# TODO-149. 戻る先が最初の画面なら「最初へ」を出さない

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort 記載なし | main（実装）+ reviewer（Sonnet 5.5 / high）+ verifier（Sonnet 5.5 / medium） |
| 実施 | Opus 5.5 / effort 記載なし | main（実装）+ reviewer（Sonnet 5.5 / high）+ verifier（Sonnet 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | 記載なし | 32 | 6,556 | 13,890 | 1,306,868 | 75% |
| reviewer | Sonnet 5.5 | high | 16 | 104 | 41,683 | 233,484 | 16% |
| verifier | Sonnet 5.5 | medium | 12 | 87 | 26,923 | 138,063 | 9% |
| 合計 |  |  | 60 | 6,747 | 82,496 | 1,678,415 | 計 1,767,718 |

- reviewer は定義のモデルが opus。条件 1 つの変更なので Sonnet 5.5 に上書きした
- verifier は定義のモデルが haiku。ブラウザを操作する実測なので Sonnet 5.5 に上書きした
- 集計はマージの前まで。マージとローカルの確認の分は入っていない

## きっかけ

2026-10-19 ユーザーの指摘。四隅の画面では「‹ 戻る」と「« 最初へ」が同じ写真の選択の画面へ戻るので、「« 最初へ」は要らない。
手で入力して開いた盤面の画面も同じなので、そこでも出さないことにした（ユーザーが選んだ）。

## やったこと

- `#to-start` を出す条件を「写真の選択の画面以外」から「`previousStep()` が写真の選択の画面でない」に変え、キーを `[s.step, s.fromPhoto]` にした別の part に分けた（`analyzer/static/app.js`）
- `index.html` のコメント、`analyzer/README.md`、`analyzer/test_pwa.py` を合わせた。analyzer 0.81.1

## 確かめたこと

- レビュー: 5 つの画面の出る／出ないが仕様どおり、キーと描画の中身はずれない（[reviewer-report.md](../agents/TODO-149/reviewer-report.md)）。古いコメントとテスト名の指摘を直した
- verifier: 写真の選択・四隅・手で入力した盤面・結果から戻った手で入力した盤面では出ず、写真から進んだ盤面・結果では出た（[verifier-report.md](../agents/TODO-149/verifier-report.md)）
- ローカル: マージ後（0.81.1・839e97d）の常駐サービスで同じスクリプトを流し、6 つとも同じ結果

## 分担の振り返り

- reviewer はコメントとテストが古いままなのと、テストが part のキーを見ていないことを見つけた。verifier は食い違いを見つけなかった
- 見込みどおりの編成で、食い違いは無い
- 次も同じでよい。前の項目の確認スクリプトを写して使い回させたので、verifier の分が小さく済んだ。画面の出し分けの確認は、前のスクリプトがあれば続けて写させる
