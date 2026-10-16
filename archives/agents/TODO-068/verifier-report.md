# TODO-068 verifier 報告

結論: 5 項目とも依頼どおりで、食い違いは無い。

1. `uv run pytest analyzer`: 84 passed（終了コード 0、95.75 秒）。
2. テストの強さ（`-k corners`、各 1 か所壊して元に戻した。最後の `git diff recognizer/corners.py` は壊す前と同一）:
   - `pin` 素通し: 2 失敗（`test_corners_keep_the_fixed_ones_and_look_in_the_trimmed_part`、`test_api_find_corners`）
   - `NEAR` の `continue` 削除: 1 失敗（`test_corners_keep_the_fixed_ones_and_look_in_the_trimmed_part`）
   - `crop` 無視（`shrink(img)`）: 2 失敗（同上、`test_api_find_corners` の TypeError）
   - `TRIMMED` を `(MIN_WIDTH, MIN_HEIGHT)` に: 1 失敗（同上）
   - `emit` の `+ at` 削除: 1 失敗（同上）
   - 補足: 5 つの壊しのうち 3 つは `test_corners_keep_the_fixed_ones_and_look_in_the_trimmed_part` 1 本だけが捕まえている。
3. PWA（390x844、`check_pwa.py` 1 回）:
   - 最初: 見つからず default（長方形）
   - 範囲を囲んだあと: [[451.2,524.9],[757.5,518.7],[754.8,780.8],[456.4,786.8]]、正解との最大ずれ 22.3 px。範囲を戻すボタンが出る
   - 隅 1 を動かして「もう一度検出」: 隅 1 は保持（True）、他は置き直し、ずれ 30.9 px（隅 1 を 12 px・隅 3 を 40 px 意図的にずらした状態を含む）
   - 範囲を戻す: crop が None、ボタンが消える
   - スクリーンショット（`3-trimmed.png`、`4-again.png`）を目で見た: 範囲を囲んだあと写真は範囲に拡大されており、四隅 4 点は遊戯面の枠の内側の角に乗っている（1 左上・2 右上・3 右下・4 左下）。`4-again.png` は隅 1 だけが意図的にずらした位置（上辺が少し傾く）。実害は未確認。
4. 検出中の離脱: Playwright で実際に確かめた（IndexedDB の読み取りだけではない）。`/find-corners` を応答させず保留し、`cornerGuess === "again"` の間に保存された履歴の `cornerGuess` が `"again"` であることを確認。ページを読み直して履歴の先頭を開くと `cornerGuess` は `"moved"`、四隅は離れたときの長方形 [[204.8,153.8],[1843.2,153.8],[1843.2,1384.2],[204.8,1384.2]] のままで、自動検出で置き直されなかった。
5. `check_corners.py`: sj1vrx 1.1%、screen2 1.6%（`--app --crop`）、photo4 `--fix 2` 4.9%（further: 1）。README の値と一致。

## 変更ファイル
`git status`: M は TODO.md、analyzer/{README.md,app.py,static/app.js,static/corners-view.js,static/index.html,static/sw.js,test_api.py}、docs/PI_CHECKS.md、recognizer/{README.md,board.py,check_corners.py,corners.py,cpu_reference.json}。未追跡は archives/agents/TODO-068/。指示の範囲との照合は、依頼に範囲の記述が無かったため行っていない（判断できない）。

## 確かめなかったこと
- 手順 4 は 1 回だけ（依頼どおり）。PWA の他のブラウザ・実機は未確認。
- 検証中の一時ファイルは scratchpad のみ。リポジトリには書いていない（このレポート以外）。
