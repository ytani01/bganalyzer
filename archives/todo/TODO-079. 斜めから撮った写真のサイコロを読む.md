# TODO-079. 斜めから撮った写真のサイコロを読む

| | main | 担当 |
|---|---|---|
| 見込み | Opus 5.5 / effort high | main（対話）/ 実装: teammate（Opus 5.5）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |
| 実施 | Opus 5.5 / effort high | main（対話）/ 切り分け: teammate + 実装: teammate（Opus 5.5。利用上限で止まり、別の teammate（Opus 5.5）が引き継いだ）+ reviewer 2 回 + verifier |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|---|---|---|---|---|---|---|---|
| main（teammate を含む） | Opus 5.5（2% は Sonnet 5.5） | high | 282 | 81,468 | 257,819 | 11,177,740 | 100% |
| 合計 |  |  | 282 | 81,468 | 257,819 | 11,177,740 | 計 11,517,309 |

- `token-usage.py TODO-079 --since '2026-10-20 14:30:00'`（TODO-180 の決着のあと）で集計。終点は 7ddc9a8（正解の直し）。
  この項目は昔に立てていて、立てたときのコミットが見つからないので `--since` で切った
- teammate は別のセッションとして動くので、担当ごとに分かれず main の行にまとまる。worktree の中で起動したセッション（引き継いだ実装の担当）は
  別のプロジェクトのログに入るので、この表に含まれない。決着の作業（7ddc9a8 より後）も含まれない
- 各担当のモデル・effort は、見込みの値のほかは記録に残っていない（Sonnet 5.5 の 2% は、どの担当かを確かめていない）

## きっかけ

`samples/photo-black-blue-oblique.jpg`（TODO-076）の 6・2 のサイコロ（小さく透明な緑）を読めなかった。
正解にサイコロのある斜め撮影のサンプル 8 枚は、どれも読めていなかった。

## やったこと

- 切り分け（`archives/agents/TODO-079/investigate-report.md`）: 斜め撮影ではサイコロの側面まで盤の面に写り、真上に直しても正方形にならないので、
  形の検出（`dice._bodies`）で落ちる。目の検出と目の並びの判定は、形さえ渡せば読む
- 2026-10-20 利用者が案 B（目の並びからサイコロを探す。今のやり方で 2 個そろわないときだけ使う）を選んだ
- `recognizer/dice.py`: `read_dice` を、読みを集める `_found` と、読みからダイスと `values` を決める `_read` に分けた。
  目から探す `_pip_found` を足した（目の候補の対の中点か片方の目を中心に正方形を置き、その中の目が面になるものを読みとする）。
  前の方法で盤の上の確かなダイスが 2 つ未満で、`values` が出ないときだけ使う（レビューの指摘で、2 つ以上見つかって読まなかったときは使わない条件を足した）。
  2 つのダイスの色の差の上限は、目から探すときだけ 15 → 25
- `analyzer/test_dice.py`（新規）: photo-black-blue-oblique を 6-2 と読む
- `recognizer/board.py`: recognizer 0.29.3 → 0.30.0
- `recognizer/accuracy_baseline.json`: photo-black-blue-oblique の dice を not read → ok
- `recognizer/README.md`: ダイスの手順 6. と、斜め撮影のサンプルの結果
- `samples/collected-brown-cream-oblique.truth.json`: ダイスの正解を 4-1 → 5-5（写真で 2 つとも上の面が 5。利用者が確かめた）

## 確かめたこと

- photo-black-blue-oblique は [6, 2]、commons-lg-cube-dice（2 人分のダイス、正解 null）は null のままで、目から探す処理は呼ばれない（evaluate で 1 枚ずつ）
- `analyzer/test_dice.py` は、目から探した結果への差し替えを止めると落ちる（verifier）
- CI の test・accuracy・ruff が通った。基準で変わったのは photo-black-blue-oblique の dice の 1 行だけで、誤読は増えていない
- reviewer の 2 回目は要修正 0、verifier は 5 項目すべて合っていた（`archives/agents/TODO-079/review2-report.md`・`verify-report.md`）

## 見送ったこと

2026-10-20 利用者が、ここでやめて決着させると決めた。測った結果は `archives/agents/TODO-079/one-pip-report.md`。

- **1 の目のせいで読めない 3 枚**（collected-black-red-oblique 3-1・collected-red-blue-oblique 6-1・collected-cream-black-oblique 3-1）。
  1 の目は目の対が無いので、目から探すやり方では面にならず、形のやり方でも側面が足されて見つからない。
  試した案は「目から探して 1 つ見つかったら、その大きさと色を手がかりに 1 の目の面を探す」。止めた理由:
  - 3 枚とも、手がかりにする 1 でない方のダイスも正しく確かに読めていない（black-red の 3・red-blue の 6 は見つからず、cream-black の 3 は 5 と読む）
  - black-red（白と赤）と red-blue（焦げ茶と赤）は 2 つのダイスの色が違う。今の読み方は、色の揃わない 2 つを 2 人分のダイスとして読まない
  - 1 の目だけの面は、側面に 1 つだけ写る目や盤の模様の点と区別する手がかりが少ない
- **側面の目まで数えて読み違えるもの**（collected-brown-cream-oblique の 5-5、collected-cream-black-oblique の 3）。
  目から探すやり方が、上の面の目の一部と側面の目を合わせて 2 や 5 と「確か」に読む。brown-cream は確かなダイスが 3 つになって null、cream-black は 1 のダイスが見つからず null。
  案として「真上の図で上の面だけの正方形の中の目を数え、側面の帯の目を外す」を出したが、試していない
- このほか、cream-red と cream-red-black は写真が粗くて目が見えず、green-red-white の 4-4 は小さな白いダイスの目の光り方で 4 を 2 個の目と見る。どれも読まないまま（誤読にはならない）

## 残ること

- 目から探すやり方の「確か」のしきい値（`MIN_READINGS = 4`）は、前のやり方と読みの単位が違うのに同じ値で、偶然の模様が確かになりうる。
  前のやり方で確かなダイスが 1 つだけのときは、目から探して別の場所に 2 つ目を作りうる。どちらも実害は見つかっていない（利用者が今のままでよいと決めた）

## 分担の振り返り

- 切り分けの担当: 崩れる段（`_bodies`）を測って示し、手で体を置けば読むことまで確かめた。案 B を選ぶ根拠になった
- 実装の担当: 目から探す道を作り、photo-black-blue-oblique を読ませた。利用上限で止まり、引き継ぎになった。全件の `check_accuracy.py --update` を既定の並列数で流し、プロセスが多く立った
- reviewer（1 回目）: 前のやり方が「わざと読まなかった」ときも目から探し直す筋と、README の段数の誤りを見つけた。どちらも直した。2 回目は要修正 0
- verifier: 2 枚の結果、テストが壊すと落ちること、値の一致を実測で確かめた。`evaluate.py --help` で全件が走りかけた
- 見込みと食い違ったところ: 実装の担当が途中で止まり、引き継ぎの担当がもう一度読み直した分が増えた。1 の目の分は、あとから利用者が足したので見込みに無かった。
  測ってみると見込みが立たず、実装せずに止めた
- 次に同じ規模なら: 実装の前に、対象のサンプル全部（ここでは 8 枚）でダイスがどこまで見つかっているかと、正解が写真と合っているかを先に測らせる。
  1 の目と色の違うダイスの組、正解の誤り（brown-cream）は、最初の測りで分かった。依頼には `--jobs=4` と「evaluate は位置引数で 1 枚だけ」を最初から書く
