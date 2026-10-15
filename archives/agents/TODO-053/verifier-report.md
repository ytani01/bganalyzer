# verifier 報告（TODO-053）

- check_accuracy.py: rc=0、`points: 572/624 (baseline 572)`、better/worse なし。一致
- trace_cpu.py check: rc=0、`0 of 26 samples read differently` / `same as the reference`。一致
- 分岐 4 通り（recognize と truth の cube を差し替えて evaluate.run を直接呼んだ。サンプルは commons-case-dice）:
  - 読み None × 正解 centre → (centre, centre) 一致
  - 読み centre × 正解なし → (None, None) 一致
  - 読み centre × 正解 black → (centre, black) 不一致、cube は None でない（WRONG）
  - 読み None × 正解 black → (None, black) 不一致かつ None（not found）
- 壊すと落ちる: if/elif を一時的に消すと rc=1、
  `WORSE: commons-lg-cube-dice: cube ok -> not found` と `WORSE: commons-rollup-oblique: cube ok -> not found`。ほかの worse なし。evaluate.py は元に戻した（差分は +6 行のまま）
- collected.py（コピーに --force）: report.md の「キューブ」は 3 行（直す前 12 の見込み。直す前は未測定）
- README の 2 か所（TODO-053）: 上の結果と食い違わない（ポイント不変、2 サンプルのキューブが ok、centre 正解の場合のみ）
- 変更ファイル: TODO.md、recognizer/README.md、recognizer/accuracy_baseline.json（lg-cube-dice と rollup-oblique の cube が not found → ok の 2 行だけ）、recognizer/evaluate.py（+6 行）、archives/agents/TODO-053/（未追跡）。指示の範囲内、余計なファイルなし

判断できなかったこと: collected の「直す前 12」は測っていない（戻して測り直していない）。

## 再確認（same_cube に移した版）

- check_accuracy.py: rc=0、572/624、better/worse なし。一致
- trace_cpu.py check: rc=0、0 of 26 samples read differently。一致
- same_cube 直接呼び出し: (None,centre)=True、(centre,None)=True、(centre,black)=False、(None,black)=False、(None,None)=True、(black,black)=True。centre×black は False で cube は None でないので WRONG。一致
- 壊すと落ちる: `or (...)` を消すと rc=1、`WORSE: commons-lg-cube-dice: cube ok -> not found`、`WORSE: commons-rollup-oblique: cube ok -> not found`。ほかの worse なし。元に戻した（`or (cube in centre ...` が 1 行あること、diff は +7 -1）
- evaluate.py 単体: `cube ok (read None, truth centre)` と元の読みが出る。一致
- collected.py: report.md の「キューブ」は 3 行。一致
- 呼び出し 3 か所（evaluate.py の __main__、check_accuracy.py:41、collected.py:57）が same_cube を使う。run() は元の読みを返す
- README: 81 行・379 行の追記は run() の補正でなく比較での扱いを指す文で、矛盾しない。389 行 rollup-oblique の「初期配置なので正解は centre」は、truth が centre で CI では ok になる結果と合う（truth.json の cube は未照合）
- 変更ファイル: 前回に加え recognizer/check_accuracy.py、recognizer/collected.py。指示の範囲内
