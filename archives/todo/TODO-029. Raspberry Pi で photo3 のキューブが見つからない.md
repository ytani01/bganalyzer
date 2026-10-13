# TODO-029. Raspberry Pi で photo3 のキューブが見つからない

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort medium | verifier（Sonnet 5.5 / medium。evaluate.py の実測）。直すことになったら reviewer（Opus 5.5 / high）も入れる |
| 実施 | Opus 5.5 / effort 不明 | reviewer（Opus 5.5 / high）+ verifier（Sonnet 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | 不明 | 156 | 26,926 | 194,488 | 5,125,020 | 89% |
| reviewer | Opus 5.5 | high | 32 | 4,007 | 57,332 | 612,448 | 11% |
| 合計 |  |  | 188 | 30,933 | 251,820 | 5,737,468 | 計 6,020,409 |

- 集計は Pi のセッションだけ。0.6.1 の直し（0ad86e1）はクラウドの別アカウントのセッションで行ったので、その分は入っていない
- verifier は集計の終点（69a416a）のあとに動いたので表に無い。完了の通知では 24,054 トークン
- verifier の定義のモデルは haiku。素材と突き合わせるサンプルが 30 枚あるので Sonnet 5.5 に上書きした
- main の effort は記録に残っておらず、不明

## きっかけ

PI-008（2026-10-14、recognizer 0.6.0）で、Pi のコンテナで evaluate.py を動かすと photo3 が
`cube not found (read None, truth centre)` になった。x86_64 では読めていた。

## やったこと

- recognizer 0.6.1（0ad86e1、クラウド）: x86_64 でも photo3 のキューブが見つかる回数が 7 回で、必要な 6 回のぎりぎりだった。
  必要な回数を 4 回に下げ、2 番目の候補の 2 倍以上も条件にした。
- 0.6.1 でも Pi では見つからなかった（2026-10-14、b709fc1）。候補を書き出して調べると、キューブの塊は 8 段階で見つかっているが、
  数字「64」が Pi では 5〜7 個の印に割れ、`1 <= marks <= 4` で全段階落ちていた。
- recognizer 0.6.2: `recognizer/cube.py` に `MAX_MARKS = 8` を置き、印の上限を 4 → 8 にした。上限 6・7・8 のどれでも Pi の全 30 枚で
  変わったのは photo3 だけだったので、余裕を持たせて 8 にした。`recognizer/README.md` の手順と当たり具合の表を更新（PR #69）。

## 確かめたこと

- verifier: ブランチのイメージで Pi の全 30 枚を測り、0.6.1 との差は photo3 の `cube not found` → `cube ok (read centre, truth centre)` の 1 行だけ。
  ポイント・バー・ホーム・ダイスは全行同じ（`archives/agents/TODO-029/`）。
- マージ後の本番（7238126）で PI-008 を確かめ直し、photo3 `cube ok (read centre)`、`/analyze-photo` 5.7 秒。PI-008 を決着させた。
- `pytest analyzer` はコンテナで 33 通過・1 失敗（イメージに git が無いための既知の `test_version_reports_both_parts_and_commit`）。GitHub Actions は通過。

## 残ること

- reviewer の指摘: 上限を 8 にしたので、Pi では commons-tavli-red-brown の重なった駒が 3 回見つかる候補になった（キューブと答えるには 1 回足りないだけ）。
  ダイスの 5・6 を止める条件は `_face_value` だけになった。誤検出は今のところ無い。
- 0.6.2 を x86_64 では測っていない。
- 範囲外: `samples/external/` の USBGF の盤面図 7 枚の正解に `cube` が無く、evaluate.py が 6 枚で `cube WRONG` を出す（盤面図にはキューブが描かれている）。

## 分担の振り返り

- reviewer は、PI_CHECKS.md と README の記述が 0.6.1 のままの所・Pi の回数と合わない所を見つけた（直した）。
  さらに自分で上限 4 と 8 を測り直し、偽の候補との差が縮んだこと（tavli-red-brown の 3 回）を見つけた。main の比較は結果の行の差だけで、これは拾えていなかった。
- verifier は期待どおりで食い違いなし。main が同じ比較を先に済ませていたので、新しく分かったことは無かった。
- 見込みとの食い違い: 原因の切り分けを main がやり、直すことになったので reviewer を足した。見込みの範囲どおり。
- 次に同じ規模なら: しきい値を変える項目では、reviewer に「結果の行」でなく「候補の回数の分布」を測らせる依頼を最初から書く。
  verifier は main の測定と重なるので、main が測った値を報告ファイルに残し、verifier にはビルドしたイメージでの再現だけを頼めば足りた。
