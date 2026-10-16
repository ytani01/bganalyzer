# TODO-068 verifier への依頼

## 目的

四隅の「もう一度検出」とトリミング（コミット前の作業ツリー）が、動くことと、テストが壊れたときに落ちることを確かめる。
背景は `TODO.md` の TODO-068、変更は `implementer-report.md` と `reviewer-report.md`（reviewer の指摘を main が直したあとの状態を見る）。

## 確かめること（各 1 回）

1. `uv run pytest analyzer` が通る（件数を書く）
2. **テストの強さ**: `recognizer/corners.py` を 1 か所ずつ壊して `uv run pytest analyzer -q -k "corners"` を流し、落ちるかを見る。壊したら必ず `git stash` ではなく手で元に戻し、最後に `git diff recognizer/corners.py` が壊す前と同じか確かめる
   - `pin(...)` を素通しにする（固定した隅を入れない）
   - `NEAR` の判定（`continue   # its corners disagree ...`）を消す
   - `find_corners` で `crop` を無視する（`img[y0:y1, x0:x1]` を `img` にする）
   - `TRIMMED` を `(MIN_WIDTH, MIN_HEIGHT)` にする
   - `emit` の `+ at` を消す
3. **PWA**: サーバーを `uv run uvicorn app:app --app-dir analyzer --port 8765` で立て、
   `BG_URL=http://127.0.0.1:8765/ OUT=<一時ディレクトリ> uv run -q --no-project --with playwright python archives/agents/TODO-068/check_pwa.py` を 1 回流す（390x844）。
   出た四隅・正解とのずれ（px）を書き、スクリーンショットを開いて、四隅の点が盤の遊戯面の角に乗っているか、範囲を囲んだあと写真がその範囲に拡大されているかを見る
4. **もう一度検出の途中で離れたとき**: Playwright で、範囲を囲んで検出が走っている最中（`state.cornerGuess === "again"` の間）にページを読み直し、
   履歴から同じ写真を開くと、四隅が自動の検出で置き直されず、離れたときの四隅のまま（`cornerGuess` が `"moved"`）かを見る。
   履歴から開く操作が難しければ、`localStorage`/IndexedDB に残った `cornerGuess` を読むだけでよい（どちらで確かめたか書く）
5. `recognizer/check_corners.py --app --crop samples/collected-sj1vrx.truth.json samples/screen2.truth.json` と `--app --fix 2 samples/photo4.truth.json` を流し、
   `archives/agents/TODO-068/README.md` の値（sj1vrx 1.1%・screen2 1.6%・photo4 の `--fix 2` 4.9%）と同じか

## 見なくてよいこと

- 全サンプルでの当たり具合の測り直し、三角形の点数の良し悪し、デザインの良し悪し
- 確かめる操作の繰り返し（どれも 1 回）

## 報告

`archives/agents/TODO-068/verifier-report.md` に、項目ごとに測った値を書く。合ったものは 1 行、食い違いだけ詳しく。
コードは直さない。原因の切り分けや、境界線上の判断はしない（「実害は未確認」と添えて報告だけ）。
返事は「終わったか・報告ファイルのパス・判断が要る点」だけにする。
