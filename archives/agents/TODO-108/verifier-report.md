# TODO-108 確認の報告（verifier）

対象: worktree `scratchpad/wt108`、ブランチ `claude/todo-108-live-view`、コミット baed05a。コードは変えていない。

## 結果

| 確認 | 期待 | 実測 | 判定 |
|---|---|---|---|
| 起動直後の `/` の読み込み回数（6 秒後） | 1 | 1（`LOAD # 1`） | 一致 |
| commit.txt を bbb に変えて 6 秒後の回数 | 2 | 2（`LOAD # 2`） | 一致 |
| live.log | `reloaded: bbb` が 1 行 | `http://127.0.0.1:8002/ at aaa` の次に `reloaded: bbb` が 1 行 | 一致 |
| さらに 6 秒後（変更後計 12 秒）の回数 | 2 のまま | 2 のまま（`LOAD` は 2 行） | 一致 |
| 窓の innerWidth / innerHeight（headless、同じ context 設定） | 412 / 915 | 412 / 915（outerWidth/Height も 412 / 915、devicePixelRatio 2） | 一致 |
| CLAUDE.md の書いたコマンドで起動（BG_URL で 8002 に向けた） | 起動して `at <commit>` を出す | `at bbb` を出し、30 秒の timeout まで動いた（exit 124） | 一致 |

- 手順 2 の live.log 全文: `http://127.0.0.1:8002/ at aaa` / `reloaded: bbb`。
- 偽サーバーのログで `/version` は変更後も続けて叩かれ、`/` の再読み込みは 1 回だけだった。

## 注記

- 手順 2 の 30 秒 timeout は、変更後 12 秒の確認を終えた時点で切れていた（exit 後の `live_view` 残存なし）。
- 手順 4 の headless 測定で、偽サーバーの `/` が 3 回目の読み込みとして数えられた（`body` に `load 3` と出た）。手順 3 の判定には影響しない。
- docs のコマンドは、書かれたとおり引数なしで起動した。既定の URL（8000 番）には触れず、`BG_URL=http://127.0.0.1:8002/` の環境変数だけを足した。8000 番のサービスには接続していない。
- `docs/raspi.md` の表の行は、`CLAUDE.md` と同じコマンドに説明を足したもので、起動の確認は上の 1 行と同じ（同じコマンドを実行）。

## 変更されたファイル（main..HEAD）

- `CLAUDE.md` +1 行（コマンドの一覧に live_view の行）
- `docs/raspi.md` +1 行（「ふだんの運用」の表に live_view の行）
- `tools/live_view.py` +51 行（新規）
- `TODO.md` 1 行（`- [ ] tools/ にスクリプトを置き…` を `- [x]` に変更）

指示の範囲（スクリプト、CLAUDE.md の一覧、docs/raspi.md の表）と合っている。TODO.md の変更はチェックの入れ替えのみ。作業ツリーは確認前後ともに clean のまま（報告ファイル `archives/agents/TODO-108/verifier-report.md` だけを追加）。

## 確かめられなかったこと・判断が要ること

- 窓の大きさは headless で測った。headful の live_view.py が開いた窓の実寸は測っていない（同じ context 設定での値）。
- 変更後の再読み込みは、`commit.txt` を書き換えて確かめた。実際の `systemctl restart` による再起動は確かめていない。
- 食い違いは無い。境界線上の判断はない。

## 使った偽サーバー

- `scratchpad/fake_server108.py`（8002 番で起動し、確認後に停止、PID 865144、ポートは解放済み）
- `scratchpad/fake108.log`、`scratchpad/live.log`、`scratchpad/docs-cmd.log`
