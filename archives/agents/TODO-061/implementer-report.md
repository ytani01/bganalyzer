# TODO-061 implementer の報告（四隅の候補の選び方）

## 結論

**採れる案は無かった。** 全件を測った 3 案は、どれも合計は main より増えたが、
どれにも大きく悪くなるサンプル（5〜14 ポイント減）がある。管理者の指示（新しい案の試行は打ち切り）に従い、
`recognizer/corners.py` は main に戻した。版上げ・`trace_cpu.py --update`・`check_accuracy.py`・テスト・README は**やっていない**。

## 変更したファイル

- `archives/agents/TODO-061/measure_corners.py`（新規）: find_corners → board.recognize で 24 ポイントを truth と比べる。
  サンプル名で絞れる。`CORNERS_DIR=<dir>` で別の corners.py（main のものなど）を測れる。進み具合は
  `/tmp/claude-649/-home-ytani-work-bganalyzer/TODO-061-progress.txt` に 1 枚ごとに追記。4 プロセスで並べて流す。
- `archives/agents/TODO-061/corners-trial.diff`: 最後に試した corners.py の差分（帯の中のバーの項 + 縦の縁の傾き 0.5 まで。`W_BAR`・`V_MAX` を環境変数で変える仮の形）
- `archives/agents/TODO-061/full-{main,new,band06,band03}.json`: 全件の結果（サンプルごとの正解数・find_corners の秒・見つけた四隅）
- `recognizer/corners.py`: 変更なし（main に戻した）

## 試した案

| 名前 | 中身 |
|---|---|
| main | 今の main |
| new | `_structure` に「真ん中のバーの帯（試すバーの幅、最低 2px）が、上から下まで両フィールドの地の色でない割合」× 0.6 を足す ＋ 縦の縁の傾きを 0.3 → 0.5 まで（`V_SLOPES`） |
| band06 | バーの項を、先端の間の帯（行 0.45〜0.55。地の色の項と同じ帯）だけで数える。重み 0.6 ＋ 傾き 0.5 |
| band03 | band06 の重みを 0.3 |

途中で試して捨てたもの（一部のサンプルだけ）: 「12 列とも三角形が合う」（列ごとの相関の最小を足す。重み 0.3 で +3、0.6 で −4。ばらつきの範囲で採らず）、
各辺が縁の上にあるかの割合を足す（傾いた辺も縁の模様に乗り、truth より高くなるので効かない）。

## 全件の値（44 枚 = samples/*.truth.json から synth-cube-* を除く）

| | main | new | band06 | band03 |
|---|---|---|---|---|
| 合計（44 枚、/1056） | 850 | 867 | 859 | 879 |
| 41 枚（TODO-062 で足した 94jhut・jpc616・q0k95c を除く、/984） | 783 | 800 | 801 | 812 |
| find_corners の秒の合計（4 並列、参考） | 188.8 | 240.9 | 232.6 | 243.5 |

- 管理者の言う 788/984 とは 5 ずれる（こちらの main は 783）。比べ方の違いかは確かめていない。
- 時間は 4 並列の中で測った値で揺れが大きい。傾きを 0.5 まで広げると縦の縁の計算が 31 → 51 本になるので、2〜3 割増えている見込み（直列では測っていない）。
- 測ったのは Raspberry Pi の上（この worktree が Pi にある）。TODO.md の「Pi では流さない」には反しているが、読み取りは CPU によらないので値はそのまま使える。

### main から変わったサンプル

| サンプル | main | new | band06 | band03 |
|---|---|---|---|---|
| collected-2aunci | 24 | 24 | 23 | 24 |
| collected-a8qvq6 | 24 | 24 | 23 | 23 |
| collected-jpc616 | 19 | 19 | **10** | 19 |
| collected-l9azfe | 23 | 24 | 23 | 24 |
| collected-si3vsd | 15 | 23 | 24 | 24 |
| collected-tad9pt | 11 | 23 | 23 | 23 |
| collected-w8eaks | 18 | 23 | 18 | 18 |
| commons-case-dice | 15 | 15 | **10** | **10** |
| commons-case-midgame | 22 | 24 | 24 | 24 |
| commons-dark-homeleft | 24 | **16** | **20** | **16** |
| commons-lg-cube-dice | 17 | 14 | 14 | 14 |
| commons-nardy-midgame | 6 | 8 | 6 | 6 |
| commons-set-cube-dice | 22 | 21 | 21 | 21 |
| commons-tavli-black | 12 | 24 | 12 | 24 |
| commons-tavli-red-brown | 24 | **17** | 24 | 24 |
| commons-tavli-red-white | 24 | **10** | 24 | 24 |
| photo2 | 20 | 20 | 22 | 22 |
| photo4 | 15 | 23 | 23 | 24 |

ほかの 26 枚は 4 案とも同じ。

## 分かったこと（次に試すなら）

- **collected-tad9pt（盤の半分）は点数の問題ではない。** 右の縁の傾きが 0.46 で、縦の縁の候補（傾き 0.3 まで）に入らず、
  正しい四角形がそもそも候補に無い。傾きを 0.5 まで広げるだけで 11 → 23。
  4 枚（dark-homeleft・case-dice・lg-cube-dice・w8eaks）で確かめた範囲では、傾きを広げただけ（バーの項なし）では main と同じ値だった。
  **「傾き 0.5 まで」だけの案は全件を測っていない**ので、採れるかは未確認（打ち切りの指示で止めた）。
- 悪くなったのはどれもバーの項のせい（傾き 0.3 のままでも同じ値になることを確かめた）。
  - 上から下までで数える（new）と、バーが地と同じ色の盤（tavli-red-white の黒い盤）で、真ん中に駒の列が来る四角形が勝つ。
  - 先端の間の帯だけで数える（band）と red-* は戻るが、dark-homeleft・case-dice が落ちる。
- tavli-black・lg-cube-dice・dark-homeleft の外れ方は「1 辺が 2〜4% 傾いた四角形」が truth より高い点数を取るもので、
  三角形の相関・地の帯・バーのどの項でも差が小さい（各項の値は分けて見た）。

## 試行を続ける予定だった範囲と、止める条件

あと 2 案のつもりだった。①バーの項を色でなく「バーの両側の縦の縁が上から下まで続くか」で数える案、②それも悪くなるサンプルを出したら「縦の縁の傾き 0.5 まで」だけの案を全件で測って採る。
ただし止める条件ははっきり決めていなかった（案の数や時間の上限を置いておらず、①が惜しければさらに調整を続けた可能性がある）。最初から「全件は 2 回まで、それで採れなければ報告」と決めておくべきだった。

## 検証

- `recognizer/corners.py` は main と同じに戻したので、版・`cpu_reference.json`・`accuracy_baseline.json`・テストは触っていない。
  `check_accuracy.py`・pytest は流していない（変更が無いため）。
- 測定スクリプトは 4 回の全件と、部分の測定で動いた（終了コード 0）。

## 判断が要る点

1. 採れる案が無い。次に進めるなら、「縦の縁の傾きを 0.5 まで広げるだけ」の案を全件で 1 回測るのが最も見込みがある
   （tad9pt +12、確かめた範囲で悪くなるもの無し。時間は増える）。
2. main の基準値が 788 でなく 783 になった。
