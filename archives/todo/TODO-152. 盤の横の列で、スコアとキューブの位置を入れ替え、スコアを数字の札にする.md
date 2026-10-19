# TODO-152. 盤の横の列で、スコアとキューブの位置を入れ替え、スコアを数字の札にする

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort 記載なし | main（実装）+ reviewer（Sonnet 5.5 / high）+ verifier（Sonnet 5.5 / medium） |
| 実施 | Opus 5.5 / effort 記載なし | main + implementer（Sonnet 5.5 / medium）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium、ブランチで 3 回）+ verifier（Sonnet 5.5、ローカルで 1 回） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | 記載なし | 88 | 24,157 | 85,670 | 4,048,557 | 46% |
| verifier | Haiku 5.5 | medium | 74 | 6,621 | 88,623 | 2,065,000 | 24% |
| implementer | Sonnet 5.5 | medium | 94 | 696 | 114,921 | 1,745,835 | 20% |
| claude-code-guide | Haiku 5.5 | 記載なし | 12 | 50 | 106,281 | 362,000 | 5% |
| reviewer | Opus 5.5 | high | 20 | 1,593 | 50,661 | 364,898 | 5% |
| 担当不明 | Sonnet 5.5 | 記載なし | 4 | 31 | 1,057 | 55,239 | 1% |
| 合計 |  |  | 292 | 33,148 | 447,213 | 8,641,529 | 計 9,122,182 |

- 集計の終点は Crawford のキューブを 40 にしたコミット（b931193）。そのあとのローカルの確認とマージ・決着の分は入っていない
- モデルは会話ログのメッセージ数から割り当てた（Opus 49 件 = main 39 + reviewer 10、Haiku 42 件 = verifier 36 + claude-code-guide 6、Sonnet 46 件 = implementer 44 + 担当不明 2）。見込みでは reviewer と verifier を Sonnet 5.5 にしていたが、ログ上は reviewer が Opus 5.5、ブランチの verifier が Haiku 5.5（定義のとおり）。ローカルの確認の verifier（Sonnet 5.5）の分は、この集計では担当不明の 2 件だけで、実際の量は取れていない
- effort は定義（`~/.claude/agents/*.md`）の値。Haiku 5.5 の effort は定義の値を写した
- claude-code-guide は組み込みで、途中の調べものに呼んだ分

## きっかけ

2026-10-19 ユーザーの依頼。盤のホーム側の横の列（TODO-151）の並びを、スコアが端でキューブが真ん中あたりだったものから、持ち主のいるキューブを上下の端、スコアを真ん中あたりに入れ替える。スコアは白地に黒い数字の正方形の札にし、クロフォードのときはキューブに Crawford と書く（どれもユーザーが選んだ）。

## やったこと

- `analyzer/static/board-view.js`: 列の並びを、上から 奥が持つキューブ・奥のトレイ・奥のスコア・中央のキューブ・手前のスコア・手前のトレイ・手前が持つキューブ に変えた（`trayY`・新設の `scoreY`・`cubeY`）。スコアは 32×32 の白地の札に数字だけ。クロフォード（`match.length > 0` かつ `crawford`）のキューブには数字の代わりに「Craw」「ford」の 2 行を書く
- `analyzer/static/style.css`: `.score-n`・`.cube-crawford` を足し、`.cube-num` を大きくした
- `analyzer/README.md`: キューブとスコアの位置の説明を新しい並びに合わせた（レビューの指摘 2 件）
- analyzer 0.85.0（`analyzer/app.py`・`analyzer/static/app.js`）。`analyzer/static/sw.js` の `CACHE` は v60 に上げた。ネットワーク優先なので上げなくても届くが、害は無いので上げたまま
- 配分の変遷: 最初は cube 28 / score 32 / tray 119 で、Crawford は 7px の字を `textLength` で詰めて 1 行に書いた。確認で画面上の字の高さが約 3.6px と読めなかったため、ユーザーの選択で 2 行に分け、さらにキューブを 28 から 40 に大きくした（tray 101、板の間隔 5、間 3。cube 40 / score 32 / tray 101 / 間 3 で 404）。字は Crawford 14px、キューブの数字 20px

## 確かめたこと

- implementer: getBBox で、ホームの左右・キューブの奥持ち／中央／手前持ち・クロフォードあり／なし・アンリミテッドで、はみ出しと重なりが無いこと。キューブを 40 にした後は、トレイに 15 枚の場合と Crawford の字がキューブの内側に収まることも数値で確かめた
- reviewer: README の古い記述 2 件を見つけた（直した）
- verifier（ブランチ、3 回）: 並び・札・Crawford の字・40 のキューブとトレイ 15 枚
- verifier（ローカル、`/version` が 0.85.0 で一致）: 手動入力の盤面で、アンリミテッド（キューブ奥持ち）では札なし、マッチ（クロフォードなし）の中央、手前持ち、クロフォードありの中央で、並びが上のとおり。スコア札のタップで sheet-match、キューブのタップで sheet-cube が開く。食い違いなし。マッチでの奥持ちは未実施（同じ `cubeY` を通る）
- `analyzer/test_pwa.py`: 31 件通った。GitHub Actions の pytest も通った

- [x] ローカル: マッチ（クロフォードあり・なし）とアンリミテッドで、盤面図の列にキューブとスコアが上の並びで出て、タップで設定が開くこと — 0.85.0 で食い違いなし

## 残ること

- クロフォードなのにキューブを片側に置ける件は TODO-153 に分けた

## 分担の振り返り

- reviewer は README の古い記述 2 件を見つけた。verifier は、最初の Crawford の字が画面で約 3.6px と読めないことを見つけた。getBBox の数値（implementer）では箱がキューブの内側に収まっていて、読めるかどうかは出なかった
- 見込みと食い違った点: 見込みは main が実装するはずが implementer を立てた。reviewer は Sonnet 5.5 の見込みが Opus 5.5 になり、verifier はブランチで 3 回（Crawford の見直しとキューブ 40 のたび）とローカルで 1 回に増えた。字の大きさを 2 度直したため
- 次に同じ規模なら、字の大きさのような見た目を決める項目では、最初の verifier への依頼に「画面での字の高さ（CSS px）を読む」を入れる。数値で収まっても読めない字は getBBox では捕まらず、直しが 2 度に割れた
- 集計では担当のモデルをログから割り当てるしかなく、見込みの行との差が見えにくい。上書きしたモデルは呼び出し側で控えておく
