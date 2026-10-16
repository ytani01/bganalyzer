# TODO-082 implementer の報告

## 変更点

- `analyzer/claude_corners.py`（新規）: `POST /claude-corners` と `claude_command()`（`BG_CLAUDE`）
  - 無効なら 404（:78）、走っているものがあれば 429（:80、モジュールの `_running` で 1 本）
  - 長辺 1568px・JPEG 90 の stream-json メッセージ（`_message`）、`claude -p` の引数は design.md どおり。cwd は空の一時ディレクトリ、`start_new_session=True`（:97）
  - 0.5 秒ごとに `request.is_disconnected()`（→ 499、:104）と `TIMEOUT` 60 秒（→ 504、:107）を見る。どの出口でも `finally` で `os.killpg(SIGKILL)` してから `wait()`（`_kill`、:64）
  - 終了コード 0 以外 → 502、返事の最後の `{"corners": ...}` が読めない → 502（`_corners`、正規表現で位置を探して `raw_decode`）
  - 縮尺を戻し、画像の中に収めて `{"corners", "width", "height"}`（送られた画像の画素）
  - ログは開始・結果（秒数、成否）を 1 行ずつ。写真と返事の本文は出さない
- `analyzer/app.py:26,46`: router を登録。`:113-115` `/version` に `"claude"`。`__version__` を 0.49.0
- `analyzer/static/app.js`: `APP_VERSION` 0.49.0。`claudeCorners()`（:757、`findAgain` と同じく `search` の番号・写真・点の動きを見てから 4 隅を置き換える。失敗は alert で、四隅はそのまま。取り消しは知らせない）。`withBusy` に `cancel` を足し、busy の表示に「取り消す」（:149、:1025）。`/version` の `claude` でボタンと注意を出す（:1157）
- `analyzer/static/api.js`: `post()` に `signal` を足した（既存の呼び出しは変わらない）
- `analyzer/static/index.html:118-119`（ボタンと「押すと写真が Anthropic に送られます」）、`:249`（取り消すボタン）。`style.css:232`（ボタンの余白）
- `analyzer/test_api.py:744-`: 偽の `claude`（tmp_path の Python スクリプト）でテスト 3 本
  - `test_claude_corners_off_or_busy`: 404・`/version` の false/true・429（`_running` を monkeypatch。子プロセスは起動しない）
  - `test_claude_corners_answer`: 200 と縮尺の戻し・画像の中に収める、壊れた返事 → 502（偽の起動 2 回）
  - `test_claude_corners_timeout_kills_it`: 504、10 秒以内に返る、偽の claude とその子の pid が両方消えている、`_running` が戻る（偽の起動 1 回）
  - 偽のコマンドの起動は合わせて 3 回。本物の `claude` は 0 回
- 文書: `analyzer/README.md`（PWA の手順 :44、`/claude-corners` の節、`/version`）、`bganalyzer.service:11-12`（コメントアウトした `BG_CLAUDE`）、`docs/raspi.md:108-`（有効にする手順）、`docs/PI_CHECKS.md` に PI-049（本物を押すのは 2 回だけと書いた）、次の番号を PI-050 に
- `TODO.md`: API と PWA のチェックを入れた。文書は CLAUDE.md が残っているので入れていない

## 検証

- `uv run pytest analyzer/test_api.py -k claude_corners -q` → 3 passed、終了コード 0
- `uv run pytest analyzer/test_api.py -k "claude_corners or version_reports or pwa_is_served or samples_off" -q` → 6 passed（版の一致のテストを含む）
- テストが壊すと落ちるか: `os.killpg` を `proc.kill()` に変えると `test_claude_corners_timeout_kills_it` が落ちる（子が pipe を握ったまま 60 秒待つため。10 秒の上限で捕まえる）。戻して通ることを確かめた
- `node --check analyzer/static/app.js`・`api.js` → 終了コード 0
- ruff（プロジェクトの設定・CI には無い）で、`app.py`・`test_api.py` の指摘の数は変更前と同じ 19。`claude_corners.py` は `File(...)` の B008 のみ（既存のエンドポイントと同じ書き方）

## 判断が要る点・残る懸念

- **`CLAUDE.md` の写真の扱いの例外は書いていない。** 担当の決まりで `CLAUDE.md` は触らないため。design.md の文面（ボタンを押したときだけ Anthropic に送る。`BG_CLAUDE` を設定したサーバーだけ。2026-10-17 ユーザーが決めた）で main が足す必要がある。TODO.md の文書のチェックもそのため未チェック
- 切断（取り消し）で子を殺す道は、TestClient では切断を起こせないのでテストしていない。PI-049 の「取り消す」で確かめる。取り消したときの状態コードは 499（クライアントはもういないので、ログに残るだけ）
- 終了コード 0 以外 → 502 の分岐はテストしていない（指示どおり起動回数を絞った。壊れた返事の 502 と同じ後処理）
- 子が自分で別のセッションに抜けた孫を作り、それが pipe を握ると `wait()` が待ち続ける（今の `claude` では起きないと見ている。実害は未確認）
- 待つ間は busy の表示が画面を覆うので、その間に点を動かす・写真を替えることは実際にはできない（`findAgain` と同じ確かめは残してある）
- `sw.js` の `CACHE` は上げていない（ネットワーク優先なので、最近の変更でも上げていない）

## 直したこと（reviewer の報告を受けて）

- 1: `_kill`（`analyzer/claude_corners.py:68-`）は `returncode` を見ずに `os.killpg`（メンバーが居なければ `ProcessLookupError`）。
  時間切れのテストの偽は「stdout を引き継いだ `sleep 60` を起こし、本体はすぐ `exit 0`」に変えた（`analyzer/test_api.py` の `mode == "slow"`）。
  504・10 秒以内・本体と子の pid が消えた、を同じ 1 本で見る。偽の起動回数は 3 回のまま。
  壊すと落ちるか: `if proc.returncode is None:` を戻すと `test_claude_corners_timeout_kills_it` が落ちることを確かめた
- 2: 返事の値が非有限なら 502（`_corners` の `math.isfinite`）
- 4: `docs/raspi.md` は `systemctl --user edit bganalyzer` の drop-in（`Environment=BG_CLAUDE=%h/.local/bin/claude`）に。`bganalyzer.service` のコメントも、ファイルは変えずに drop-in で足す形に
- 5: ルートの `README.md` の図（`app.py` のエンドポイントに `/claude-corners`、`claude_corners.py` の箱と矢印）と表に 1 行
- 6: PI-049 のスマホの行に、Funnel 越しで取り消したあと Pi で `pgrep -af claude` とログの `cancelled` を見る手順を足した。
  本物を押す回数を 2 回のままにするため、Pi（127.0.0.1）での取り消しはやめ、Pi は点が置かれるのを見る 1 回、取り消しはスマホの 1 回にした
- 7: docstring と `docs/raspi.md` を、同時 1 本と 60 秒の打ち切りだけで、続けて押す回数に上限は無い（公開サーバーではだれでも利用枠を使える）と書いた
- 8: Claude で置き換えたら `cornersFixed` を全部 false に（`analyzer/static/app.js` の `claudeCorners`）
- 9: 起動の `OSError`（パスが違う・実行できない）は 502 と `could not start claude: <strerror>`、ログにも 1 行
- 作り込みすぎ: 待つループを `while not (await asyncio.wait({reply}, timeout=0.5))[0]:` の 1 行に、`reply.cancel()` を条件なしに、`_kill` の `returncode` の条件を削除、`busy-cancel` の `e.stopPropagation()` を削除。`width`・`height` は残した

### 検証（直したあと）

- `uv run pytest analyzer/test_api.py -k claude -q` → 3 passed、終了コード 0
- `node --check analyzer/static/app.js`・`api.js` → 終了コード 0
- ruff（参考。CI には無い）: `claude_corners.py` は B008 の 1 件だけ（既存のエンドポイントと同じ書き方）
- 壊したときの試しで残った `sleep 60` は PID を確かめて止めた（ほかに残っていない）

### 残る懸念

- 非有限の値と起動の `OSError` の 502 はテストしていない（偽の起動回数を増やさないため。どちらも短い分岐）
