# TODO-082 の設計（main）

目的: 四隅の画面に「Claude に選ばせる」ボタンを置き、押すとサーバーが `claude -p` に写真を渡して四隅を答えさせ、その位置に点を置く。

## 決まったこと（ユーザー、2026-10-17）

- モデルは Sonnet 5.5（`claude-sonnet-5-5`）。環境変数で変えられるようにする
- ボタンは `claude` が使えるサーバーでだけ出す（環境変数で有効にする）。押したときだけ写真が Anthropic に送られる
- 子プロセス: 時間の上限で殺す、端末が切れたら（取り消したら）殺す、同時に走らせる数を絞る

## 試しの結果（`try_claude.py`・`try_claude.txt`）

呼び方はこれで固める（`try_claude.py` の `ask()` がそのまま手本）:

- 写真を長辺 1568px 以下に縮め（`cv2.INTER_AREA`）、JPEG（品質 90）を base64 にして `--input-format stream-json` の user メッセージの image ブロックで渡す。ツールは使わせない
- `claude -p --model <model> --input-format stream-json --output-format stream-json --verbose --tools "" --no-session-persistence --setting-sources "" --effort high`、cwd は空の一時ディレクトリ
  - `--setting-sources ""` で利用者の設定・hook を読まない（入力 2.3 万 → 約 6 千トークン）。そのとき effort を明示しないと考えずに答えて大きく外れる
- プロンプトは `try_claude.py` の `PROMPT`。角ごとに 1 行説明させてから最後の行に JSON を書かせる（考えずに答えると外れる）
- 返事は stdout の `"type": "result"` の行の `result`。その中の最後の `{"corners": ...}` を読む（空白の入り方に頼らず正規表現などで）
- 結果: ずれの最大は長辺の 0.7〜3.2%、1 回 7〜9 秒

## API（`analyzer/app.py`、または新しいモジュール `analyzer/claude_corners.py`）

- 環境変数
  - `BG_CLAUDE`: `claude` コマンドのパス。**設定されたときだけ有効**（`BG_SAMPLES_DIR` と同じやり方）。systemd のユーザー unit は PATH に `~/.local/bin` を含まないのでパスで渡す。テストはここに偽のコマンドを置く
  - `BG_CLAUDE_MODEL`: 既定 `claude-sonnet-5-5`
- `/version` に `"claude": true/false` を足す（PWA はこれでボタンを出す）
- `POST /claude-corners`（form: `image`）→ `{"corners": [[x,y]×4], "width", "height"}`（送られた画像の画素。TL, TR, BR, BL。画像の中に収める）
  - 無効なら 404。走っているものがあれば待たせず 429（同時は 1 本。公開しているサーバーなので、人の利用上限を食われないよう絞る）
  - 子プロセスは `asyncio.create_subprocess_exec(..., start_new_session=True)`。終わらせるときは `os.killpg` でグループごと（claude は子を持つ）。殺したあと `wait()` して残さない
  - 時間の上限 60 秒 → 504。端末が切れたら（`await request.is_disconnected()` を待ちと並べて見る）殺して終わる
  - 返事が読めない・終了コードが 0 でない → 502（detail に短い理由。写真や返事の全文は log に出さない）
- ログ: 起動と結果（かかった秒数、成否）を 1 行ずつ

## PWA（`analyzer/static/`）

- 四隅の画面の「もう一度検出」の行に「Claude に選ばせる」ボタン。`/version` の `claude` が true のときだけ出す
- 押すと待つ間の表示（今の `busy` の表示で足りれば使う）と「取り消す」。取り消しは `AbortController` で fetch を止める（サーバーは切断で子を殺す）
- 返ってきたら 4 隅をすべて置き換える（送った画像の縮尺を戻す。`findAgain` と同じく、待つ間に写真を替えた・点を動かしたなら置かない）。失敗は短い文で知らせ、四隅はそのまま
- ボタンの近くに注意の一文「押すと写真が Anthropic に送られます」
- analyzer の版を 0.49.0 に（`app.py` の `__version__` と `app.js` の `APP_VERSION`）

## 文書

- `CLAUDE.md` の写真の扱いに例外を 1 つ足す（ボタンを押したときだけ Anthropic に送る。`BG_CLAUDE` を設定したサーバーだけ。2026-10-17 ユーザーが決めた）
- `analyzer/README.md` の API の節に `/claude-corners`、環境変数
- `bganalyzer.service` にコメントアウトした `Environment=BG_CLAUDE=...` の行、`docs/raspi.md` に有効にする手順（Pi で `claude` にログイン済みであること）
- `docs/PI_CHECKS.md` に Pi で確かめる項目（有効にしてボタンが出る、photo6 で押して点が置かれる、取り消すと子プロセスが残らない）

## テスト（`analyzer/test_api.py`）

本物の `claude` は呼ばない。`BG_CLAUDE` に偽のコマンド（tmp_path に書いた Python のスクリプト）を置く:
- 正しい JSON を返す → 200 と四隅（縮めた分の倍率が戻っている）
- 無効 → 404、`/version` の `claude`
- 返事が壊れている → 502、時間切れ（上限を monkeypatch で短く）→ 504 で子が残っていない
- 同時 2 本目 → 429
