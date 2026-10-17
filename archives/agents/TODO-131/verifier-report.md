# TODO-131 確認報告

## 走らせたもの

1. 作業ツリーのコードを `uv run uvicorn app:app --app-dir analyzer --host 127.0.0.1 --port 8031` で起動（PID 1343029）。`/version` は `{"analyzer":"0.73.1","recognizer":"0.24.0","commit":"f75b704","samples":false,"claude":false}`。終了後、PID を kill し、ポート 8031 が閉じたことを確認。
2. `archives/agents/TODO-131/measure.py`（`uv run -q --no-project --with playwright python`、`connect_over_cdp("http://127.0.0.1:9222")`）で、新しい context（412×848、is_mobile、has_touch）を作り、`http://127.0.0.1:8031/` を開いた。live_view の既存ページは操作していない。
3. `#file` に `samples/` の jpg を先頭から 5 枚入れ、そのたびにページを開き直して写真の画面に戻した。最近の写真は 1 → 5 件と増えた。
4. 写真の画面で `evaluate` により次を読み出した。
5. 写真の画面のスクリーンショットを `archives/agents/TODO-131/photo-screen.png` に保存し、目視で確認した。

終了コード: measure.py は 0。

## 測った値（最近の写真 5 件、写真の画面）

```
docScrollHeight: 848
innerHeight: 848
listClientHeight: 336
listScrollHeight: 422
liCount: 5
historyVisible: true
historyBottom: 697.28125
liFirstTop: 328.78125
liFirstHeight: 78
hdrVersion: "a0.73.1 · r0.24.0 · f75b704"
step: "photo"
```

## 合否

- `scrollHeight <= innerHeight`: 848 <= 848。収まる（ページ全体はスクロールしない）。
- `.history-list` の `clientHeight` が 336、`scrollHeight` が 422 で、336 より大きい。5 件目は一覧の中でスクロールする。
- 版の表示は `a0.73.1`。指示どおり。

## スクリーンショットの目視

- 一覧は 4 件分が見え、5 件目は下で切れて一覧内のスクロールバーが出ている。
- 「写真を撮る」「写真を選ぶ」「手で入力」、「うまく読み取るコツ」、「最近の写真」の見出し、一覧、注記 2 つが欠けたり重なったりしていない。

## 食い違い・注意

- 版の文字列の末尾が `f75b704`。これは HEAD のコミット ID で、作業ツリーの未コミットの差分を表すものではない。版の番号は 0.73.1 で合っている。
- 計測スクリプトの `wait_for_function` が毎回 60 秒でタイムアウトした（`wait failed at 1`〜`5`）。原因は、写真を入れた後は写真の画面が出ていないので一覧が描き直されず、件数の待ちが永久に満たされないこと（推定）。ただし、ページを開き直した後の件数はいずれも正しく 1〜5 件に増えていて、測った値には影響しない。

## 差分の範囲（git status / git diff）

- 変更ファイル: `TODO.md`、`analyzer/app.py`、`analyzer/static/app.js`、`analyzer/static/style.css`。
- `style.css`: `.history-list` の `max-height` を `calc(10 * 78px + 9 * 8px)` から `calc(4 * 78px + 3 * 8px)` に変更。同じ行のコメントも「4 rows (TODO-131)」に変わった。これは指示の範囲。
- `analyzer/app.py` の `__version__` と `analyzer/static/app.js` の `APP_VERSION` を 0.73.0 から 0.73.1 に上げた。CLAUDE.md の「analyzer の版を上げる」の規則どおり。指示の範囲と合う。
- `TODO.md`: 指示の項目のチェックを `[x]` にした。CLAUDE.md の「実装できた時点で入れる」の規則どおり。指示の範囲外のファイルではない。
- 指示に無いファイルの変更は無い。新規の `archives/agents/TODO-131/` は、今回の確認で作ったもの（measure.py、photo-screen.png、server.log、server.pid、verifier-report.md）。

## 確かめられなかったこと・判断できなかったこと

- 測ったのは 412×848 の 1 つの条件だけ。ほかの画面の大きさや、写真の画面の表示が変わる他の要素（注意書きの長さなど）は確かめていない。
- 「最近の写真」の件数は 5 件だけ測った。件数がさらに多いときも同じ（一覧内スクロール）になることは、CSS の `overflow-y: auto` と `max-height` から読み取れるが、実測はしていない。
- スマホの実機で確かめたわけではない（Chromium のエミュレーション）。
- テスト全体（pytest）、認識・解析、accuracy は、指示により流していない。
- 実害の有無の判断はしていない。指示の合否（収まるか・一覧が 4 件分で切れるか）だけを判定した。
