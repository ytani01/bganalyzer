# TODO-181 implementer 報告

## 変更
- `analyzer/static/style.css:306`: 背景・色・4px の `var(--accent)` の枠・角丸・影（`0 8px 28px #000b`）を `.palette, .sheet` の共通の規則に出した。`.sheet` の元の行（位置・幅・余白など）はそのまま
- `analyzer/static/style.css:220`: `.palette` は位置・`z-index`・幅 232px・余白 8px だけ残した（枠・影の値は共通の規則へ移動）
- `analyzer/app.py:48`・`analyzer/static/app.js:14`: 0.94.1 → 0.94.2
- `TODO.md`: TODO-181 のチェック 2 つ（CSS・版）を入れた。`- [ ] ローカル:` は残している

## 検証
- `uv run ruff check`: 成功（All checks passed）
- `uv run ruff format --check`: 成功（58 files already formatted）
- 画面の確認は verifier が行う（実測していない）

## 判断が要る点・懸念
- 全体が `box-sizing: border-box` なので、吹き出しの幅 232px は変わらず、枠が 1px → 4px になった分、中身の幅が 6px 狭くなる（駒の数の 4 列ボタンが少し細くなる）。JS の位置計算は `offsetWidth` を使うので位置はずれない。verifier に、ボタンの幅と中身が崩れていないかを見てもらう
- 影が `0 6px 20px #0004` → `0 8px 28px #000b` に変わる（`.sheet` と同じ値）
