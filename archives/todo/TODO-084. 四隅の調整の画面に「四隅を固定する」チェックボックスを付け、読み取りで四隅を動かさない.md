# TODO-084. 四隅の調整の画面に「四隅を固定する」チェックボックスを付け、読み取りで四隅を動かさない

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort high | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |
| 実施 | Opus 5.5 / effort high | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | high | 102 | 26,106 | 115,124 | 5,011,335 | 80% |
| verifier | Haiku 5.5 | medium | 30 | 9,432 | 61,220 | 592,782 | 10% |
| reviewer | Opus 5.5 | high | 26 | 125 | 58,453 | 546,324 | 9% |
| 合計 |  |  | 158 | 35,663 | 234,797 | 6,150,441 | 計 6,421,059 |

- reviewer・verifier とも定義（`~/.claude/agents/`）のモデルと effort のまま
- 集計は着手（2026-10-17 02:26）からで、立てたときの相談の分は入れていない。reviewer の output は少なめに出ている（サブエージェントのログの欠け）

## きっかけ

ユーザーの要望（2026-10-17）: 四隅を正確に合わせても、読み取りが枠の辺と三角に合わせ直して四隅を動かすので、合わせた意味が薄い。
photo6 では正解の四隅を渡しても、辺に合わせる段階で 50px ほど動いた（TODO-083）。

決めたこと（2026-10-17 ユーザー）: 四隅の調整の画面に「四隅を固定する」チェックボックスを付ける。チェックしていたら、読み取りで四隅を動かす処理
（枠の辺に合わせる段と、三角に合わせ直す `refine_tips`）を全部省き、渡した四隅で正規化した盤から列の位置だけを合わせて駒を読む。
着手時に決めたこと: チェックは既定で外しておき、四隅の点を手で動かしたら自動で入れる（外すこともできる）。

## やったこと

- `recognizer/board.py`: `recognize(..., keep_corners=True)` で `refine` 2 回と `refine_tips` を省き、渡した四隅の射影で `fit_columns` を 1 回だけ（`fit` の段は `by="corners"` で 1 回）。CLI に `--keep-corners`。recognizer 0.23.0
- `analyzer/app.py`: `/analyze-photo` に `keep_corners`。analyzer 0.50.0（`APP_VERSION` も）
- `analyzer/static/index.html`・`app.js`: 四隅の画面に `#keep-corners`。点を置く・動かすと入り、新しい写真・画像の編集・「もう一度検出」で見つかったとき・Claude の四隅で外れる。最近の写真の記録に写真ごとに残す。「ざっくりで大丈夫です」の文言は、チェックを外すよう促す説明に替えた
- `analyzer/test_photo_view.py`: 固定すると `fit` が 1 回で、四隅が送ったまま返るテスト
- 文書: recognizer/README.md（「四隅を固定して読む」と測定の表、`--keep-corners`）、analyzer/README.md（API の項目、PWA の説明、段の数）、`scan.js` のコメント、docs/PI_CHECKS.md に PI-050

## 確かめたこと

- 正解の四隅でアプリと同じく縮めて読んだ一致数（24 ポイント中）: photo6 18 → 14、photo5 22 → 16、commons-case-midgame 24 → 22、commons-leather-cups 15 → 18。固定すると 4 枚中 3 枚で下がった
- reviewer: 既定の読みは前と同じ。指摘のうち「もう一度検出」で外す件と、文書の段の数の例外を直した。指で触っただけ（動かさない）でも入る件は、cornersMoved と同じ扱いとしてそのままにした
- verifier: テスト 12 件が通る。photo6 の行を再現。PWA でタップするとチェックが入り、固定して読むと四隅の差 0、外すと最大 17.5px 動き、写真を選び直すと外れる（`archives/agents/TODO-084/verifier-report.md`）

## 残ること

- Pi での画面の確認（docs/PI_CHECKS.md の PI-050）
- 正解の四隅でも固定すると読みが下がることが多い。点を少し動かしただけで入るので、ざっくり合わせたまま固定して読む恐れがある（説明には外すよう書いた）

## 分担の振り返り

- reviewer は「もう一度検出」でチェックが残る漏れと、文書 3 か所の段の数の書き漏れを見つけた。verifier は食い違いを見つけなかった（実装どおりであることの実測）
- 見込みと同じ編成で、食い違いは無い
- 次に同じ規模（recognizer の小さな分岐 + PWA の状態 1 つ）なら同じ編成でよい。verifier の PWA の確認は、手順を依頼で細かく書けば Haiku 5.5 でも実際のクリックで測れた
