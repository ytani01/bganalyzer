# verifier への依頼（TODO-139）

**目的:** `git diff main -- recognizer/` の直しで、t0480x の黒の駒が読めるようになり、足した分岐を外すと元に戻ることを実測する。
**手段:** `uv run python recognizer/board.py` と `uv run python recognizer/evaluate.py <truth.json を名指し>`。一時的にコードを書き換えたら、終わったら `git diff` が依頼時と同じに戻っていること。

**測ること（各 1 回）**
1. `uv run python recognizer/board.py collected/user-1792344322479-t0480x.jpg --corners 240,259,1758,228,1772,1641,254,1686 --home right --bottom-colour 1 | head -5`
   期待: ポイント 19 が 5B、12 が 5B、10 が 1B、17 が 3B。ポイント 1 は空（四隅の項目で扱うので、これで合格）
2. `recognizer/radial.py` の `PEAK_REL` を 0.25 に戻して 1 と同じコマンド → 期待: 19 が空に戻る
3. `recognizer/checkers.py` の、`alike` から円を足すループの `len(chain) >= 2` を `len(chain) >= 99` にして 1 と同じコマンド → 期待: 12 が空か 1B に戻る
4. 同じく `0.3 * pitch < depth` を `-9 * pitch < depth` にして `uv run python recognizer/evaluate.py samples/commons-wooden-dice.truth.json` → 期待: ポイント 11 が got -4（元の版では -3）
5. 戻した版で `uv run python recognizer/evaluate.py samples/commons-wooden-dice.truth.json samples/commons-dark-homeleft.truth.json samples/screen1.truth.json`
   期待: 13/24、24/24、24/24、wooden-dice のポイント 11 は got -3

**しないこと:** 全サンプルの evaluate / check_accuracy（CI が流す）。コードの直し。境界線上の判断は報告だけにする。
**報告:** `archives/agents/TODO-139/verifier-report.md`。項目ごとに、実際に出た行を貼る。期待どおりは 1 行、食い違いだけ詳しく。返事は「終わったか・報告のパス・判断が要る点」だけ。
