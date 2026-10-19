# TODO-169 implementer の報告

## 変更点
- `analyzer/static/result.js`: 候補手の一覧（`<ol class="moves">`）の前に `<h3>この目で動かした後</h3>`、勝率の表の前に `<h3>ダイスを振る前</h3>`。
  候補手が空（動かせる手が無い）のときと、ダイスが無いときは前者を出さない。勝率の表の見出しは `game_over` 以外で常に出る。
- `analyzer/static/style.css`: `.result h3`（結果の画面に小見出しの class が無かったため、最小限で追加）
- `analyzer/test_pwa.py`: `test_result_headings_say_when_the_numbers_are_for`。順序と、ダイスが無いとき前者が出ないことを見る
- `analyzer/app.py`・`analyzer/static/app.js`: 0.92.0 → 0.92.1
- `analyzer/README.md`: 結果の画面の説明に 2 つの見出しを追記
- `TODO.md`: TODO-169 の実装のチェックを入れた

## 検証
- `uv run pytest analyzer/test_pwa.py`: 36 passed
- 壊すと落ちるか: 「この目で動かした後」を消すと 1 failed（戻して 36 passed）
- `uv run ruff check`: 通過 / `uv run ruff format --check`: 通過

## 残る懸念
- 計算・数字・文言（TODO-166・167）は変えていない。画面での見た目（h3 の大きさ・色）は未確認で、ローカルの確認で見る。
- `sw.js` の CACHE 番号は上げていない（直近の result.js の変更でも上げていなかったため）。
