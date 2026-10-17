# TODO-108. スマホの大きさの Chromium で開き、更新のたびに再読み込みする

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort high | main（実装）+ verifier（Haiku 5.5 / medium） |
| 実施 | Opus 5.5 / effort high | main（実装）+ verifier（Haiku 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | high | 74 | 26,124 | 39,053 | 10,563,716 | 88% |
| verifier | Haiku 5.5 | medium | 74 | 3,242 | 60,781 | 1,379,338 | 12% |
| 合計 |  |  | 148 | 29,366 | 99,834 | 11,943,054 | 計 12,072,402 |

- verifier は定義（`~/.claude/agents/verifier.md`）のモデル・effort のまま（haiku / medium）。追加分の確認も同じ担当に続けて頼んだ
- TODO-107 と並行して進めたので、範囲にはそちらの分も入っている

## きっかけ

ユーザーが、スマホの大きさの Chrome で画面を開いておき、更新のたびに再読み込みできるかを尋ね、Playwright の画面付き Chromium で `/version` を見る案を選んだ（2026-10-17）。
着手後に、verifier が画面で確かめている様子もこのブラウザで見られるようにすることを足した。

## やったこと

- `tools/live_view.py`: 画面付きの Chromium（`/usr/bin/chromium`）を 412×915（スマホの設定、Service Worker は止める）で開き、2 秒おきに `/version` の `commit` を見て、変わったら再読み込みする。サービスの再起動中（読めない間）は待つ。窓を閉じると終わる。URL は引数で変えられる
- `live_view.py` は Chromium を `--remote-debugging-port=9222` 付きで起動する。`tools/pi_ui_check.py`・`tools/ui_snapshot.py` は環境変数 `BG_CDP` があれば `connect_over_cdp` でそのブラウザにつなぎ、自分の窓を開いて操作する（終わるとその窓だけ閉じる）。無ければ今までどおり見えない Chromium
- `CLAUDE.md` のコマンドの一覧と、`docs/raspi.md` の「ふだんの運用」に使い方を書いた
- 作業ツリーは TODO-107 の verifier が使っていたので、別の worktree で作った

## 確かめたこと

- verifier（`archives/agents/TODO-108/verifier-report.md`）: 偽のサーバー（8002 番）で、`commit` が変わらない間は再読み込みせず、変わると 1 回だけ再読み込みし、`reloaded: bbb` が出る。画面の大きさは 412×915。追加分は、`BG_CDP` 付きの `pi_ui_check.py speech` が live_view のブラウザに窓を開いて OK になり、終わると live_view の 1 つだけに戻る。付けなければ今までどおり OK
- PR #323 の GitHub Actions の `test` が通った
- ローカル: live_view を開いたまま PR #323 をマージすると、サービスの再起動のあと `reloaded: 73f334e` が出て再読み込みされた（前は 19f6808）

## 決めたこと

- 決着のときにユーザーが、これからアプリの画面を見せる場面ではスクリーンショットの代わりに live_view のブラウザを操作して見せる、と決めた。`CLAUDE.md` の「アプリの画面を見せるとき」に書いた

## 分担の振り返り

- verifier は食い違いを見つけなかった。偽のサーバーで commit を差し替える方法で、再読み込みの回数を数えられた。追加分で、別の live_view が 9222 番を使っていたこと（main が試しに起動したもの）に気づき、止めずに待った
- 見込みと食い違わなかった。追加分は同じ担当に続けて頼み、計測の組み直しが要らなかった
- 次に道具を作る項目では、作る前に「確認の様子を見たいか」を聞いておく。着手後に足すと、確認を 2 回に分けることになる
