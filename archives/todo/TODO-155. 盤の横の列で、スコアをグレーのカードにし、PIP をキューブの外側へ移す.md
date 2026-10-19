# TODO-155. 盤の横の列で、スコアをグレーのカードにし、PIP をキューブの外側へ移す

|      | main | 担当 |
|------|------|------|
| 見込み | Sonnet 5.5 / effort medium | implementer（Sonnet 5 / medium）+ reviewer（Opus 5 / high）+ verifier（Sonnet 5.5 / medium。定義は Haiku なので上書き） |
| 実施 | Opus 5.5 / effort 記載なし | implementer（teammate、Sonnet 5.5 / effort 記載なし）+ reviewer（Opus 5.5 / 記載なし）+ verifier（Sonnet 5.5 / 記載なし） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main（implementer の teammate の分を含む） | Opus 5.5 + Sonnet 5.5 | 記載なし | 122 | 22,494 | 114,319 | 2,886,614 | 100% |
| 合計 |  |  | 122 | 22,494 | 114,319 | 2,886,614 | 計 3,023,549 |

- 集計は `~/.claude/bin/token-usage.py TODO-155`（始点 22:58、終点は作業の最後のコミット 23:04）。reviewer と verifier は終点より後に動いたので入っておらず、実際より少ない。teammate の会話ログは main の行にまとまって出る（モデル別では Opus 5.5 が 57%、Sonnet 5.5 が 43%）
- verifier は定義が Haiku だが、画面の操作を伴うので Sonnet 5.5 に上書きした（見込みのとおり）

## きっかけ

盤の横の列で、スコアとキューブがどちらも白い角丸の四角に黒い数字で、区別が付けにくかった。PIP は盤の上の各プレイヤーの行に札で出していた。

## やったこと

- `analyzer/static/board-view.js`: スコアを、列の幅いっぱいの角を丸めないグレー（`#c4c4c4`）の札にした（キューブは変えない）。PIP は、盤の上の行の札をやめて、列の両端（キューブの外側。奥は上、手前は下）に「PIP」と数字の 2 行の札で出すようにした。`ROW`・`rowY` を `COL.pip`・`pipY` に替え、`VIEW` を列の上下の PIP まで含む高さに組み直した。PIP をタップして持ち主を入れ替える動き（`onPart` の `"colour"`）は同じ
- `analyzer/static/style.css`: `.pip-n` を 20px にし、「PIP」用の `.pip-l` を足した
- analyzer を 0.87.0 に上げた（`analyzer/app.py`、`analyzer/static/app.js`）
- `analyzer/README.md` の PIP とスコアの説明を、今の表示に合わせた
- PR #461（マージ e45dd50）

## 確かめたこと

- `analyzer/test_pwa.py` 32 件が通った。GitHub Actions の `test` も通った
- verifier が PR のコードを live_view のブラウザ（スマホの大きさ）で動かし、マッチあり（キューブ中央・奥・手前）、アンリミテッド、PIP のタップ、結果の画面を画像で見た。スコア・PIP・キューブは重ならず、欠けも無かった。盤の上に古い PIP の札は残っていない
- reviewer が列の並びを式から計算し、どのキューブの位置でも PIP と 3 離れて重ならないこと、`VIEW` が札を収めること、タップの対応が変わっていないことを確かめた。古いコメントと報告の記述の食い違いが見つかり、直した
- ローカル（開発機、マージ後）: 更新後の http://127.0.0.1:8000/ の版が `a0.87.0 · r0.28.0 · e45dd50` に上がり、盤面の画面の列にグレーのスコアと両端の PIP が出て、キューブが中央・奥・手前のどれでもスコアや PIP と重ならないことを画像で見た

## 分担の振り返り

- **見つけたこと:** reviewer は古いコメント 2 か所を見つけた（`ROW` を消したあとの「奥の行」）。verifier は、PIP をタップすると PIP の数字が入れ替わらず変わる（奥 160 / 手前 167 → 208 / 215）と報告した。持ち主を入れ替えると向きが逆になって数え直すだけで、今までと同じ動きだった
- **見込みと食い違った理由:** 見込みは subagent の定義での名前だったが、実際は teammate で動かした。確認と決着までを同じ担当（implementer）に続けて頼んだ
- **次に同じ規模なら:** 表示だけの変更なので、同じ組み方でよい。ただし、README の古い記述は implementer が先に洗い出せるので、最初の依頼に「`rg` で文書の該当箇所も直す」と入れておくと 1 往復減る
