# TODO-082 verifier 報告

本物の claude は呼んでいない（偽: scratchpad の `fake_claude`、`ui.py`、`srv.sh`）。画面 390x844、photo6.jpg（2048x1685、サーバーが 1568 に縮める）。

1. `uv run pytest analyzer/test_api.py -k claude -q`: 3 passed、終了コード 0
2. curl
   - 偽が NaN を返す: 502 `{"detail":"could not read the corners in Claude's answer"}`、`/version` は `"claude":true`
   - `BG_CLAUDE=/nonexistent/claude`: 502 `{"detail":"could not start claude: No such file or directory"}`
   - `BG_CLAUDE` なし: `/version` は `"claude":false`、`/claude-corners` は 404 `this server does not ask Claude`
3. Playwright
   - `BG_CLAUDE` なし(8766): `claude-corners` と `claude-note` の hidden は両方 true。あり(8765): 両方 false。注意の文は「押すと写真が Anthropic に送られます」
   - 押す: 待つ表示「Claude が四隅を選んでいます…」、「取り消す」の hidden は false。応答 200。置いた点 `[[681,788],[1592,612],[1559,1282],[466,1341]]`、truth との差は全隅 x・y とも 0（最大 0）。`cornerGuess` は `found`、`cornersFixed` は全部 false
   - 遅い偽(10 秒)で取り消す: 取り消しの 0.5 秒後に偽のプロセス（走行中は PID 459231）が消えた。点は取り消し前と同じ。続けて押すと 200（429 にならない）
   - 隅 0 をドラッグ: `cornersFixed` = [true,false,false,false]、点 [824.0, 902.4]。Claude で置き換え後は `cornersFixed` が全部 false、点 [681,788]
   - 画面: `archives/agents/TODO-082/verifier-corners.png`。ボタン「Claude に選ばせる」と注意の文は欠けず、重なっていない

## 食い違い・補足

- 取り消したあとの `cornerGuess` は `moved`（点は変わらない）。設計の「点が変わらない」とは合う。この値が適切かの判断はしない
- スクリーンショットは四隅の画面に入って 1.5 秒後で、上の文は自動検出中の「盤の四隅を探しています…」のまま。ボタンは検出中でも押せる状態で出ている（実害は未確認）
- 自分の作業の失敗: 偽のスクリプトの最初の版は cwd 相対でサンプルを読んで exit 1 になり、直して取り直した（上の値は直した後）。`kill $(pgrep -f ...)` が自分のシェルを巻き込んだが、サーバーは PID で止めて、8765・8766・偽のプロセスが残っていないことを `pgrep` で確認した（8000 の既存サービスは触っていない）
- 偽は truth を縮尺で返すので、点が truth と完全一致するのは偽の性質による。確かめたのは縮尺の戻しと置き換えの流れで、Claude の精度ではない
- 変更ファイル: CLAUDE.md、README.md、TODO.md、analyzer/README.md、analyzer/app.py、analyzer/static/{api.js,app.js,index.html,style.css}、analyzer/test_api.py、bganalyzer.service、docs/PI_CHECKS.md、docs/raspi.md、新規 analyzer/claude_corners.py、archives/agents/TODO-082/。設計の範囲外のファイルは無い
