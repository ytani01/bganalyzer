# verifier 報告（TODO-028 k-means 整数化、Pi で実測）

1. check_corners.py 1 回目: exit=0。23 枚のずれ・見つからない・最後の行「within 3.6%: 7, further: 11, not found: 5」は README「0.11.1（Pi）」列と全 23 枚一致、最後の行も「7 / 11 / 5」に一致。
   - **食い違い（時間）**: README は「Pi で 1 枚 0.1〜1.8 秒」。実測は 0.22〜2.44 秒（1 回目）。1.8 秒を超えたもの: rollup-oblique 2.44、leather-cups 2.30、case-midgame 2.06、burl 1.84（1 回目）。2 回目も leather-cups 2.16、case-midgame 1.97 が超過。下限 0.1 秒は未達（最小 screen1 0.17）。実害は未確認。全体は 30.4 秒 / 26.0 秒。
2. 2 回続けて実行: 23 枚の値（ずれ%・見つからない）は完全一致、最後の行も同じ。時間だけ揺れる（rollup-oblique 2.44→1.56 など）。
3. pytest（docker）: 45 passed, 8 skipped, 1 warning（76 秒）。通る。
4. 壊すと落ちるか: rsync -a --exclude .git で scratchpad/copy に写し、corners.py の `PCG64(0)` を `PCG64(1)` に変更（56 行目の 1 か所）。`-k same_on_every_cpu` で:
   `FAILED analyzer/test_api.py::test_corners_are_the_same_on_every_cpu`、1 failed
   `AssertionError: commons-dark-homeleft` / `[147.4, 153.9] != [184.4, 153.1]`（先頭の dark-homeleft で落ちた）。落ちる。
5. 元の作業ツリー: 私は変更していない。git status は指示どおりの 5 ファイル（TODO.md, analyzer/test_api.py, recognizer/README.md, recognizer/board.py, recognizer/corners.py）＋ archives/agents/TODO-028/ のみ。

注: README の列の見出しは「0.11.1（Pi）」（上で「0.11.0」と書いたのは誤記。0.11.1 列と照合した）。
確かめなかったこと: x86_64、コードの良し悪し。
