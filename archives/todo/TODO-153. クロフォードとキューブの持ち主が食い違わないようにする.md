# TODO-153. クロフォードとキューブの持ち主が食い違わないようにする

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort 記載なし | main（判断）+ implementer（Opus 5.5 / medium）+ reviewer（Sonnet 5.5 / high）+ verifier（Sonnet 5.5 / medium、live_view のウインドウで `BG_CDP` を付けて操作） |
| 実施 | Opus 5.5 / effort 記載なし | main（判断）+ implementer（Opus 5.5 / medium）+ reviewer（Sonnet 5.5 / high、2 回）+ verifier（Sonnet 5.5 / medium、ローカルで 1 回） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| implementer | Opus 5.5 | medium | 196 | 3,016 | 155,275 | 5,184,295 | 36% |
| main | Opus 5.5 | 記載なし | 136 | 23,429 | 89,516 | 4,569,427 | 32% |
| verifier | Sonnet 5.5 | medium | 98 | 7,841 | 116,853 | 3,482,369 | 24% |
| reviewer | Sonnet 5.5 | high | 40 | 351 | 82,682 | 1,042,215 | 8% |
| 合計 |  |  | 470 | 34,637 | 444,326 | 14,278,306 | 計 14,757,739 |

- 集計の終点は `analysis.py` にコメントを足したコミット（5b0c8aa）。そのあとのマージ・ローカルの確認・決着の分は入っていない
- 同じ範囲に出た claude-code-guide（input 12 / output 2,826 / cache_creation 74,781 / cache_read 208,343）は TODO-154 の調べものなので、表と合計から除いた
- モデルは管理者が起動したときの指定。機種別の集計では haiku-5-5 が 45 件出ていて、担当別の件数と合わない（verifier の定義のモデルは haiku）。どの担当の分かはログからは決められなかった
- effort は定義（`~/.claude/agents/*.md`）の値。reviewer の定義のモデルは opus、verifier は haiku で、どちらも Sonnet 5.5 に上書きした

## きっかけ

2026-10-19 ユーザーの依頼。クロフォードなのにキューブを奥か手前に置けて、エラー（`CRAWFORD_CUBE`）で知らせているだけだった。食い違う状態そのものを起こさないようにする。

## やったこと

決めたこと（ユーザーが選んだ）:

- 後の操作に合わせる。クロフォードを入れたらキューブを中央へ戻し、キューブを片側にしたらクロフォードを外す。キューブが片側のまま値だけ変えても外す
- 写真を開き直したときと、写真からキューブが片側に読めたときは、写真の方を後の操作とみなして、知らせずにクロフォードを外す
- 食い違いに届く経路が無くなったので `CRAWFORD_CUBE` は消す

変えたもの（analyzer 0.86.0）:

- `analyzer/static/app.js`: `setCube`・`setMatch` で互いに合わせる。`startPhoto` と読み取り（`recognize`）で、キューブが片側ならクロフォードを外す。読み取りでは盤面を入れた後に外し、サーバーの `analysis_error` が Crawford の件ならその alert は出さない（ほかの理由は今までどおり出す）。`crawfordCube`・`CRAWFORD_CUBE` を消した
- `analyzer/analysis.py`: app.js がこのエラーの文言の `Crawford` を見ていることをコメントに書いた
- `analyzer/README.md`・`analyzer/static/index.html`: 「解析する」が灰色になる条件と、クロフォードの説明を今の動きに合わせた
- `analyzer/test_pwa.py`: app.js から `setCube`・`setMatch`・`startPhoto`・`recognize` を切り出し、Node で 11 通りを動かすテストを足した
- `analyzer/app.py`・`analyzer/static/app.js`: 0.86.0

## 確かめたこと

- implementer: 新しいテストが、6 通りの壊し方（読み取りの alert を常に出す、`startPhoto` の条件の反転、読み取りの条件の反転、`setCube` で片側のまま値を変えたときに外さない、ほかの理由でも黙る、盤面を入れる前に外す）でそれぞれ落ちること
- reviewer（1 回目）: 古い文書 3 か所と、壊しても落ちないテスト 4 通りを見つけた。どちらも直した。2 回目は通った
- verifier（ローカル、`/version` が analyzer 0.86.0・commit 66e1674）: 5 ポイントマッチ・白 4 黒 0 で、クロフォードを入れる・キューブを片側にする・クロフォードのまま screen-app-green-far を読み取る、を各 1 回。どれも期待どおりで alert なし。読み取りの後は「解析する」で解析できた
- `analyzer/test_pwa.py`: 32 件通った。GitHub Actions の pytest も通った

- [x] ローカル: クロフォードを入れるとキューブが中央に戻り、キューブを片側にするとクロフォードが外れること — 0.86.0 で食い違いなし（指での操作は DOM 経由のクリック・change イベントで代えた）

## 分担の振り返り

- implementer は、保存済みの食い違いが入る経路（写真の開き直し・読み取り・手番の変更）を洗い出し、`CRAWFORD_CUBE` を消せるかの材料を出した。reviewer は、文書の古い記述 3 か所と、文字列を見るだけで壊しても落ちないテスト 4 通り、alert の抑え方が広すぎる点、`await` の前でクロフォードを外していた点を見つけた。verifier は食い違いを見つけなかった
- 見込みと食い違った点: reviewer が 2 回になった。最初のテストが `setCube`・`setMatch` しか動かさず、`startPhoto` と読み取りの分岐を文字列で見ていたため。ユーザーの決定が 3 回に分かれて届き（保存済みの扱い、alert の有無）、implementer への追加の依頼も 3 回になった
- 次に同じ規模なら、implementer への最初の依頼に「分岐を足した関数はすべて Node で動かして確かめ、壊すと落ちることを報告に書く」を入れる。文字列の assert で済ませたテストが reviewer の 2 回目を呼んだ。調べてから決めることは、implementer の調査の報告を受けてからまとめてユーザーに聞くと、追加の依頼が 1 回で済む
