# TODO-178 verifier 報告

対象: worktree `impl-178`、コミット `04d0f70`。コードは変えていない（`git status` は空）。

## 実施
- `uv run uvicorn app:app --app-dir analyzer --host 127.0.0.1 --port 8001` を起動（`/version` は analyzer 0.94.3、commit 04d0f70）。確認後に停止し、起動ログにエラーは無し。
- `tools/live_view.py http://127.0.0.1:8001/` を起動し、CDP（9222）で接続。
- 390x844 の新しいタブで `samples/collected-blue-red-top.jpg` を `#file` に入れ、四隅の画面（`#corners`）まで進めた。
- 測定は `getBoundingClientRect` の値（px、ビューポート基準）。

## 結果

| # | 確かめたこと | 結果 |
|---|---|---|
| 1 | 行の位置（横から撮ったオフ） | 一致。`.canvas-wrap` bottom 396 < `#corner-opts` top 404（行は bottom 448）< `#turn-tools` top 456 |
| 1' | 横から撮った（オン）で `#side-from-row` が行の下に出る | 一致。`#side-from-row` top 456 / bottom 517。`#turn-tools` top 525 より上。チェックは入った（`checked: true`） |
| 2 | `#claude-note` が DOM に無い、「Anthropic に送られ」が画面の文字に無い | 一致（`claudeNoteInDom: false`、`anthropicTextAnywhere: false`）。`analyzer/static/` の検索でも該当なし |
| 3 | `#edit-start` が `#turn-tools` の最初の子 | 一致（`editStartIsFirstChild: true`） |
| 4 | `#corner-reset` の文言 | 一致（「四隅をクリア」） |
| 5 | ヘッダーの analyzer の版 | 一致（「a0.94.3 · r0.29.3 · 04d0f70」） |
| 6 | 「画像を編集」で `#corner-opts` が隠れ、「やめる」で戻る | 一致。編集中は `#corner-opts`・`#side-from-row`・`#turn-tools`・`#corner-tools` が hidden（top 0）、`#edit-tools` が表示（top 427）。`#edit-cancel` の後は `#corner-opts` top 404、`#side-from-row` top 456 に戻った |

- 「確定」の後の挙動は確かめていない（「やめる」で戻ることだけ確認）。

## 画面（スクリーンショット）
- `/home/ytani/tmp/playwright-mcp/todo178-corners.png`（横から撮ったオフ、全画面）
- 欠け・重なりは無し。写真、チェックの行、回転・編集の行、四隅をクリア・再検出の行、ゲームの選択、下部の「戻る」「盤面を読み取る」が順に並んでいる。デザインは評価していない。

## 確かめられなかったこと・判断が要ること
- 判断が要る点は無し。
- 横から撮ったをオンにしたときの初回の質問（端末に覚える仕組み）は、今回の確認の範囲外として扱った。
- `tools/live_view.py` は、この確認のために起動した（ブラウザの窓が開いたまま）。残すか閉じるかは管理者に任せる。
