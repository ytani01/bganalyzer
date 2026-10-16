# TODO-065 の確認の依頼（verifier）

目的: アプリのアイコンの差し替えが指示どおりかを確かめる。コードは直さない。境界線上の判断は報告だけ。

対象: `git diff main -- analyzer/` （icon.svg・icon-192.png・icon-512.png・app.py・app.js・sw.js）

確かめること（それぞれ 1 回でよい）:
1. `rsvg-convert -w N -h N analyzer/static/icon.svg` で作った PNG と、コミット前の作業ツリーの `icon-192.png`・`icon-512.png` が画素で一致するか（`magick compare -metric AE` の値を載せる）
2. 192px の PNG と、`icon.svg` を 16px・32px に描いた PNG を開いて見て、欠けていないか・余計なものが映っていないか・虫眼鏡（黄色い輪と黒い縁、中は緑）が見分けられるか
3. `icon-512.png` は manifest で maskable にも使っている。虫眼鏡全体が中心から半径 205px（40%）の円に収まるか（`icon.svg` の座標から計算し、計算を載せる）
4. `analyzer/app.py` の `__version__` と `analyzer/static/app.js` の `APP_VERSION` が両方 0.51.0、`sw.js` の `CACHE` が `bganalyzer-v55`
5. `xmllint --noout analyzer/static/icon.svg` が通る

やらないこと: デザインの良し悪しの評価、pytest、アプリの起動、他の静的ファイルの確認。

報告: `archives/agents/TODO-065/verifier-report.md` に、一致したものは 1 行、食い違いだけ詳しく。返事は「終わったか・報告ファイルのパス・判断が要る点」だけ。
