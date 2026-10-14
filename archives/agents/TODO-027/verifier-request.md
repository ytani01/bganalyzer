# TODO-027 verifier への依頼

## 目的
ブランチ `claude/todo-027-dark-checkers-impl`（PR #112、コミット eb49710）の recognizer が、Raspberry Pi で次のとおり読むことを実測で確かめる。
コードは直さない。原因の切り分けや、境界線上の判断はしない（見つけたことを報告するだけ）。

## 測り方（この Pi、作業ディレクトリ /home/ytani/work/bganalyzer）
- `uv run` は gnubg で落ちるので、次の形で動かす:
  `uv run -q --no-project --python 3.12 --with opencv-python-headless --with numpy python recognizer/evaluate.py <truth.json ...>`
- main の recognizer は `git archive origin/main recognizer | tar -x -C <scratch>` で取り出し、`<scratch>/recognizer/evaluate.py samples/*.truth.json` のようにサンプルのパスを渡して動かす
  （パスを渡さないと、置いた場所の ../samples を探して何も測らない）。

## 確かめること
1. `samples/*.truth.json` 23 枚: ブランチの正しいポイントの合計が 505、main が 492。サンプルごとに、ポイント・bar・home guess・dice・cube の判定が
   main より悪くなったものが無い（期待: 変わるのは dark-homeleft 12 → 22、set-cube-dice 12 → 15 だけ）
2. `collected/user-*.truth.json`（ai1 の盤、4 組）: ブランチの合計が main（75）を下回らない（期待: 24・19・14・18）
3. 同じ円が重なって出ても落ちない: `board.cv2.HoughCircles` を、元の結果を 2 回つなげて返すものに差し替えるスクリプトを 1 本作り
   （`archives/agents/TODO-027/dup_hough.py` に置く）、commons-rollup-oblique と commons-dark-homeleft を読んで例外が出ないこと。
   さらに、そのスクリプトを main の recognizer に向けても落ちないかは見なくてよい
4. 壊すと落ちるか: `recognizer/board.py` の `TEX_SHOWN` を 100（捨てない）、`TEX_HIDDEN` を 0（足さない）にした一時コピーで 1. を測り、
   dark-homeleft が 22 より下がることを確かめる（一時コピーは scratch に作り、リポジトリのファイルは変えない）

## 見なくてよいもの
- しきい値の良し悪し、コードの書き方（レビュー済み）
- `accuracy_baseline.json`（x86_64 で測る決まりなので、別に CI の値で直す）
- README・TODO の文面

## 報告
`archives/agents/TODO-027/verifier-report.md` に、項目ごとに測った値（サンプル名と数値）を書く。期待どおりの項目は 1 行、食い違いだけ詳しく。
返事は「終わったか・報告ファイルのパス・判断が要る点」だけにする。
