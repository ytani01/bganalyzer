# TODO-139. 盤の端とバーの隣の列で、黒の駒を数え落とす（対応しない）

| | main | 担当 |
|---|---|---|
| 見込み | Opus 5.5 / effort high | main（切り分け・実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |
| 実施 | Opus 5.5 / effort high（途中から medium） | main（切り分け・実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | high → medium | 92 | 37,758 | 88,375 | 5,596,797 | 80% |
| reviewer | Opus 5.5 | high | 42 | 4,151 | 75,876 | 1,040,684 | 16% |
| verifier | Haiku 5.5 | medium | 20 | 2,212 | 38,279 | 272,886 | 4% |
| 合計 |  |  | 154 | 44,121 | 202,530 | 6,910,367 | 計 7,157,172 |

- `token-usage.py` の終点が途中の `feat(recognizer): …（TODO-139）`（2b9eff9）になったので、そのあとの CI の切り分けと明暗を分ける案の分は入っていない
- main の effort は、利用者が作業の途中で `/effort medium` にした
- reviewer・verifier は定義（`~/.claude/agents/`）のまま（reviewer は opus / high、verifier は haiku / medium で Haiku 5.5）

## きっかけ

`collected/user-1792344322479-t0480x`（Backgammon Galaxy をモニターごと撮った写真）で、黒のポイント 1（1 個）・12（5 個）・19（5 個）が抜け、11 個が上がり扱いになっていた。正解は写真と合っている。

## やらないと決めた理由

円の候補の探し方を変えずには t0480x を直せず、変えるとほかの写真が悪くなった。利用者がここで止めると決めた（2026-10-19）。

- 原因: `radial.py` は、いちばん強い山（白い駒）の 25%（`PEAK_REL`）に届かない山を捨てる。この写真の暗い黒の駒は 21〜24% で届かない。
  ポイント 12 の駒はさらに下の暗い三角形と同じ色で、重なった駒の縁が出ず（`support` 0.55〜0.72）、最初の判定で捨てられる
- 試した案と結果（詳細は `archives/agents/TODO-139/README.md`）
  - `PEAK_REL` 0.2 と「確かな駒から枠まで同じ色の円が駒 1 個分ずつ並べば足す」決まり: t0480x は 19・12 が直ったが、CI の accuracy で 8 組が悪くなった（合計 1327 → 1324）。悪くしたのは `PEAK_REL` 0.2 のほう
  - 山を足す決まりだけ: ほかの組は変わらないが、t0480x のポイント 12 が候補に入らないので直らない
  - 明るい円と暗い円で別々に `PEAK_REL` を当てる: t0480x も、ほかの 3 組も悪くなった
  - 縁の勾配の基準を甘くする（ポイント 1 向け）: commons-dark-homeleft のポイント 19 が崩れた
- ポイント 1 は四隅のずれ（番号の行まで囲む）も絡むので、TODO-140 で扱う

## 確かめたこと

- reviewer（`archives/agents/TODO-139/reviewer-report.md`）: 足す円の枠側の下限が無く、commons-wooden-dice の空いたポイント 11 が -3 → -4 になる。条件を足して直した
- verifier（`archives/agents/TODO-139/verifier-report.md`）: t0480x の読みと、分岐を外すと戻ることを確かめた（項目 4 は依頼の期待値の誤り）
- PR #416 の CI: `test` は通り、`accuracy` は落ちた

## 残ること

- t0480x は直っていない。写真がたまったら、TODO-030 のポイントごとに駒の数を当てるモデルで扱う

## 分担の振り返り

- reviewer は枠側の下限の抜けを実測で見つけた（CI では捕まらない種類）。verifier は分岐を外したときの戻りを確かめ、期待値の誤りも報告した
- 見込みとの食い違い: 実装は想定どおりだったが、全サンプルでの影響を CI で見るまで分からず、reviewer・verifier の確認が捨てる差分に対するものになった
- 次に同じ規模で、しきい値のように全サンプルに効く定数を変えるときは、reviewer・verifier を起こす前に CI の accuracy を 1 回流し（push して約 3 分）、通ってから担当を起こす
