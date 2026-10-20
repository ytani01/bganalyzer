# TODO-179 implementer の報告

## 変更点

- `recognizer/import_collected.py:37` `MARGIN = 0.1` を足した
- `recognizer/import_collected.py:103-110` `paint`: 四隅を四隅の平均（盤の中心）から外へ 1.1 倍に広げた四角の外を黒くする。写真の外へはみ出す分は `cv2.fillPoly` が写真の端で切る
- `recognizer/import_collected.py:13` docstring の説明を合わせた
- `analyzer/test_collected.py:208-210` 既存のテストから「四隅のすぐ外（3px）が黒い」の確かめを外した（広げたので成り立たない。中が元のままの確かめは残す）
- `analyzer/test_collected.py:211-` `test_paint_leaves_10_percent_around_the_board_and_stops_at_the_edges` を足した（左・上・右の境目の内外と、写真の左にはみ出す四隅）
- `samples/collected-*` 20 組を塗り直した（下）。写真の大きさ・四隅の座標・`*.truth.json` は変えていない
- `recognizer/accuracy_baseline.json` を `check_accuracy.py --update --jobs=4` で書き直した
- `recognizer/README.md:59` 集めた写真の行: 1392 ポイント中 1196 → 1181（`import_collected.table_row` で作り直した）
- `CLAUDE.md:51-53`「変えないもの」: 塗る範囲（10% 広げた四角の外）と、周りの手や物が写りやすくなる点を書いた
- `TODO.md` TODO-179: 「何を決めるか」の段落を消し、背景に「塗り直しは開発機で行う」を 1 行足した。ローカルの行までチェックを入れた
- `archives/agents/TODO-179/repaint.py`: 塗り直しに使ったスクリプト。`samples/collected-*.truth.json` の `id` と `collected/user-*-<id>.truth.json` を `import_collected.sample_id` で対応させ、`paint` で塗り直す

## 塗り直した組

`collected/` に元の写真があったのは 22 組。そのうち 20 組を塗り直し、2 組は元に戻した（判断が要る点を参照）。

塗り直し前後の画像（左が前、右が後。リポジトリには入れていない）:

- `/home/ytani/tmp/playwright-mcp/todo179/collected-green-felt-side-hand.jpg`
- `/home/ytani/tmp/playwright-mcp/todo179/collected-app-grey-shot.jpg`
- `/home/ytani/tmp/playwright-mcp/todo179/collected-blue-red-top.jpg`
- `/home/ytani/tmp/playwright-mcp/todo179/all-after.jpg`（塗り直した 20 組の一覧。人の顔が新たに写った組は見当たらない。手は元から写っている -hand の組だけ）

対応が正しいことは、盤の中の画素の差で確かめた（各組とも 1 画素あたり平均 0.5 以下。JPEG の書き直し分）。

## 精度（基準の変化）

合計 2064 ポイント中 1814 → 1799（-15）。良くなった 4 組・悪くなった 7 組:
diagram-bw-far 18→21、red-blue-far 14→20、tan-black-side-3 16→18、wood-side（bar・cube が ok に）、
app-grey-shot 24→21（cube WRONG に）、black-red-oblique 24→21、carved-tan-oblique 19→15、cork-green-side 12→11（bar が外れる）、
galaxy-screen-7 24→14（home が外れる）、green-felt-side-hand 16→12、tan-red-side 13→12（home は当たるように）。
盤の周りが残って実際の写真に近づいた分の変化で、読み取りのコードは変えていない。

## 検証

- `uv run pytest -q analyzer/test_collected.py` → 13 passed（終了コード 0）
- `MARGIN = 0.0` に戻すと新しいテストが落ちることを確かめた（1 failed）
- `uv run ruff check` → All checks passed、`uv run ruff format --check` → 58 files already formatted
- `uv run python recognizer/check_accuracy.py --update --jobs=4` → 終了コード 0、1799/2064 points
- 誤って `check_accuracy.py --help`（引数を見ないので全サンプルの確認として走る）を流し、途中で止めた。結果は使っていない

## 版

上げない。`import_collected.py` は `samples/` へ取り込む道具で、アプリ（PWA・API）の読み取りの結果は変わらないため（CLAUDE.md の「バージョン」の、測る道具だけの変更と同じ扱い）。

## ローカルの確認

要らないと判断した。アプリの画面と読み取りは変わらない。新しい塗り方は、次に読み違いの組が自動で取り込まれたときに使われる。

## 判断が要る点

1. **「10% 広げる」の読み方。** 盤の中心から各隅までの距離を 1.1 倍にした（盤の幅・高さがそれぞれ 10% 大きくなる。各辺の外に 5% ずつ残る）。「各辺の外に盤の大きさの 10% ずつ残す」（1.2 倍）の意味なら `MARGIN = 0.2` にして塗り直しをやり直す
2. **collected-galaxy-screen-9 は塗り直さなかった。** TODO-175 で利用者の指示により塗っていない元の写真にしてあり（7ff61f2）、`analyzer/test_corners.py` も使っている
3. **collected-tan-black-side-1 は塗り直さなかった。** 2026-10-16 に手で入れた組（524d9de）で、今の写真は盤の右上の外が手で塗られている。新しい幅で塗ると右上に人の肌（顔か腕）が出る（`/home/ytani/tmp/playwright-mcp/todo179/collected-tan-black-side-1.jpg`）。塗り直すなら、その部分を手で塗る必要がある

## 残る懸念

- black-red-oblique の上の縁に、指のようなものが小さく写っているかもしれない（一覧の縮小画像で見た限り。実害は未確認）
- 精度の合計が 15 ポイント下がる。CI の `accuracy` は書き直した基準と比べるので落ちない見込み
