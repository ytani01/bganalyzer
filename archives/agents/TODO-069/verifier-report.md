# verifier-report TODO-069

- `uv run pytest analyzer`: 84 passed, 3 warnings (fork の DeprecationWarning のみ)、終了コード 0。
- 変更ファイル: TODO.md, analyzer/README.md, analyzer/app.py, analyzer/static/app.js, analyzer/static/board-view.js, analyzer/static/sw.js。指示の範囲と合っている（指示に無いファイルの変更なし）。
- 画面 390x844、home right、1 回の実測。手前: 上がり 3、奥: 上がり 2（盤に 12 個 / 13 個）、キューブ=奥 4、ダイス 6-5、手前が振る。最善手 `6/off 5/off`。スクリーンショット: board.png（盤面の確認/修正）、result.png（解析結果）。局面は page.evaluate で state に直接設定し、解析は実際に #analyze を押して実行。
  - ヘッダーの版 v0.46.0: 一致
  - 手前のトレイ=下の行・右端（home 側）、数字 3 と 3 枚: 一致
  - 奥のトレイ=上の行・右端、数字 2 と 2 枚: 一致
  - キューブ（奥の行の左端、4）: 一致
  - トレイ・キューブ・数字が点の番号や盤と重ならない、欠けない: 一致
  - 横はみ出し: 両画面とも scrollWidth が innerWidth 以内（実測）
  - 上がる矢印の先がトレイの中: 一致（result.png の拡大で 2 本とも先端がトレイ内）
- 気になる点（実害は未確認、判断は管理者）:
  - 5 から上がる矢印の曲線が、下の行の点番号「4」の上を横切る。読めなくなるかは確認していない。
- 確かめていない: キューブが centre（下の行のバーの真下に 64）、home left、上がり 15 枚の幅。
