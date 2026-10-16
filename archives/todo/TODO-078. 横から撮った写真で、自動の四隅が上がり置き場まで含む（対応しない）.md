# TODO-078. 横から撮った写真で、自動の四隅が上がり置き場まで含む

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort high | main（測定・実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |
| 実施 | Opus 5.5 / effort high | main（測定・実装）+ reviewer（Opus 5.5 / high、2 回）+ verifier（Haiku 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | high | 90 | 25,248 | 168,517 | 3,654,355 | 69% |
| reviewer | Opus 5.5 | high | 52 | 4,249 | 133,443 | 1,269,134 | 25% |
| verifier | Haiku 5.5 | medium | 22 | 3,598 | 38,015 | 281,638 | 6% |
| 合計 |  |  | 164 | 33,095 | 339,975 | 5,205,127 | 計 5,578,361 |

- 集計は `--since '2026-10-16 23:19:39'`（直前の main のコミット）。着手は /clear の直後
- reviewer・verifier は定義（`~/.claude/agents/`）のまま。Agent ツールで model と effort を同じ値で明示した

## きっかけ

`PXL_20240608_005725204.jpg`（TODO-076）を回した写真で、自動の四隅の右の辺が上がり置き場の外まで出て、左上が上にずれる。
盤の外を黒く塗った `samples/photo5.jpg` では四隅が見つからない。

## やらないと決めた理由

切り分けの結果（`archives/agents/TODO-078/stages.py`・`score.py`）: photo5 の奥の辺は傾き約 0.36 で、`SLOPES` の上限 0.3（17°）の外のため、
奥の辺の候補に一度も入らない。正解の四隅の `_structure` の点数（1.03）は見つけた四隅（0.88〜0.90）より高く、点数の付け方ではなく候補の拾い方で外れている。

試した直し（どれも採らず、コードは戻した。2026-10-16 ユーザーが決めた）:

| 案 | photo5 | 全サンプル（within 3.6% / further / not found。main は 35 / 17 / 4） |
|---|---|---|
| 奥・手前の辺の傾きを ±0.5 に広げる | 4.7% | 未測定（reviewer: 急な線の重複が候補 6 本を埋める） |
| ＋重複を写真の真ん中の位置で間引く | 3.1% | 未測定（commons-tavli-red-white 1.9% → 5.0%） |
| ＋重複を左端と右端の両方で近い線だけ間引く | 3.5% | 32 / 21 / 3（screen1 2.5% → 7.0%、collected-o32w4i 1.7% → 32.2% など） |
| 今の 6 本は変えず、0.3〜0.5 の線を 2 本足す | 4.2% | 悪化した 5 枚で screen1 15.3%、collected-o32w4i 36.5% |
| `_move_in` の内への幅 5% → 8%・10%、候補 6 → 10 本 | 悪くなる・揺れる | 未測定 |

急な線を候補に入れると、ほかの盤で間違った四角形が点数で勝つ。直すには点数の付け方から見直す必要があり、TODO-067 の範囲になる。
photo5 では、見つかっても上下の辺がケースの外の縁に寄る（内側の縁は暗い枠と暗い盤面の境で弱い）。

## 確かめたこと

- 切り分けは photo5 と塗る前の写真（回したもの）の 2 枚で、`find_corners` の段ごとの絵と `_structure` の点数を見た（`archives/agents/TODO-078/stages.py`・`score.py`）
- 直しの案は photo5・commons-rollup-oblique・commons-tavli-red-white など数枚で比べ（`three.sh`）、3 つ目の案は verifier が全サンプルで main と比べた（`before.txt`・`after.txt`・`verifier-report.md`）。screen1 で `test_api.py` の四隅のテストも落ちた
- コードの変更（`corners.py`・版・README・テスト）はすべて戻した

## 分担の振り返り

- reviewer は 1 回目で「急な線の重複が候補を埋める」ことと、commons-rollup-oblique の変化を見つけた。2 回目で、真ん中で間引く案が commons-tavli-red-white を崩すことを見つけた。どちらも main の数枚の試しでは拾えなかった
- verifier は全サンプルで悪化を見つけ、これで採らないと決まった。見込みでは「直して悪くならないことを確かめる」役だったが、実際は案を捨てる根拠になった
- 食い違い: 見込みは「候補の拾い方を直せば済む」だったが、急な線を入れると点数の付け方の弱さが出て、TODO-078 の範囲では直せなかった
- 次に同じ規模なら: 候補を増やす案は、数枚で試したあとすぐに全サンプルで一度測る（`check_corners.py` は数十秒で済む）。reviewer の 2 回分を待つ前に、悪化の有無を先に見る
