# TODO-178 implementer 報告

## 変更
- `analyzer/static/index.html`: チェックボックスの行と `#side-from-row` を新しい `#corner-opts` に包み、写真（`.canvas-wrap`）と `#turn-tools` の間へ移した。`#edit-start` を `#turn-tools` の左端へ。`#corner-reset` の文言を「四隅をクリア」に。`#claude-note` の行を削除。
- `analyzer/static/app.js`: `#claude-note` の出し入れを削除（`$("claude-corners").hidden = !v.claude;`）。画像編集中は `#corner-tools` と同じく `#corner-opts` も隠す（元は `#corner-tools` の中にあったため。挙動を保つ）。`APP_VERSION` 0.94.2 → 0.94.3。
- `analyzer/app.py`: `__version__` 0.94.3。
- `analyzer/README.md`: ボタンの並びと「やり直す」の文言を合わせた。
- `TODO.md`: 実装した 5 項目にチェック（ローカルの行は未チェック）。

## 検証
- `uv run pytest analyzer/test_side.py analyzer/test_pwa.py analyzer/test_photo_view.py`: 67 passed
- `uv run ruff check`: 通過 / `uv run ruff format --check`: 通過
- 画面は未確認（verifier が live_view で確認する）。

## 懸念・範囲外
- `#corner-opts` の id と、それを編集中に隠す JS を足した（チェックボックスを `#corner-tools` の外へ出すため。足さないと画像編集中も残る）。
- `tools/ui_snapshot.py` は `#corner-reset` を id で押すので影響なし。`docs/raspi.md` の Anthropic の記述は別の説明文で、触っていない。
