# verifier 報告（TODO-076）

1. 3 枚の読み（1 回ずつ、`uv run python recognizer/evaluate.py samples/<名前>.truth.json`）。基準 `accuracy_baseline.json` の 3 行と一致。
   - photo5: 22/24（home 誤り +16.1、dice 読めず、cube ok）。基準 points 22 / home false / dice "not read" / cube ok と一致
   - collected-er0y2w: 21/24（cube not found）。基準と一致
   - commons-nardy-midgame: 16/24。基準と一致
2. 壊すと落ちる: `geometry.ROW_REACH = 99`（分岐を効かなくする）で photo5 を `evaluate.run` で読むと 10/24。22 から 12 下がる。落ちる。
   （スクリプト: /tmp/claude-649/x/b.py。ファイルは書き換えていない）
3. 版: `recognizer/board.py` の `__version__` = "0.22.1"。`git diff main --stat -- analyzer` は空（app.py・app.js は変更なし）。
4. samples/photo5.jpg: 4624×3472、`getexif()` は空。1000px に縮小して目視: 手・腕・顔は写っていない。盤の外側は黒で塗られ、写真は斜めに切り出されている。

差分のファイル（git diff main --stat）: TODO.md、archives/agents/TODO-076/{README.md,reviewer-report.md,why_dropped.py}、recognizer/{README.md,accuracy_baseline.json,board.py,geometry.py}、samples/photo5.{jpg,truth.json}。指示（refine_tips の分岐、photo5 追加）の範囲内。

確かめなかったこと: 全サンプル・テスト全体・文書の文面（指示どおり）。
判断が要る点: なし。
