# TODO-056 reviewer 報告

対象: `git diff main`（ブランチ claude/systemd-instead-of-docker、未コミット）と未追跡の `bganalyzer.service`。
実測はこの Pi（rpi5-1、Debian 12 bookworm、`bganalyzer-app-1` が動いている本番）で読み取りだけ行った。何も変えていない。

## 要修正

### 1. docs/raspi.md:39-41 / 48 — uv を入れた直後のシェルでは `uv` が見つからない

- 問題: 「1. Pi の準備」で `curl -LsSf https://astral.sh/uv/install.sh | sh` を流したあと、「2.」の `uv sync --frozen` をそのまま続けると、
  同じシェルでは `uv: command not found` になる。インストーラーは `~/.local/bin` に入れ、PATH は次のログインか
  `source $HOME/.local/bin/env` で効く。
- 根拠: 消した Docker の手順には「入れたらログインし直す」と書いてあった（差分の削除行）。新しい手順にはそれに当たる一文が無い。
  インストーラーの挙動は uv の公式の説明による（この Pi で入れ直しての実測はしていない）。
- 「書いたとおりに実行して動くか」の観点で、そのままでは止まる。

### 2. tools/check_pi.py:52-53 — 比べる対象から `Dockerfile`・`compose.yaml` を外したが、`bganalyzer.service` を足していない

- 問題: この一覧は「Pi で何かし直す必要がある変更」を見るためのもので、以前は配備の定義（Dockerfile・compose.yaml）も入っていた。
  配備の定義は今は `bganalyzer.service` なのに、一覧に入っていない。
- なぜ問題か: unit を変えても、Pi の更新手順（`git pull && uv sync --frozen && systemctl --user restart bganalyzer`、
  CLAUDE.md:13・docs/raspi.md:96・docs/PI_CHECKS.md:13）は `~/.config/systemd/user/` のコピーを入れ直さない。
  `docker compose up -d --build` は compose.yaml を毎回読み直していたので、この抜けは今回の切り替えで新しく生じたもの。
  check_pi.py も「code changed: none」と出して気づけない。
- 対で直すもの（判断は管理者）: check_pi.py の一覧に `bganalyzer.service` を足すことと、docs/raspi.md の「ふだんの運用」に
  「`bganalyzer.service` が変わったら `sed` と `daemon-reload` からやり直す」を書くこと。今は「フォルダを移したら」（raspi.md:55）しか書いていない。

## 検討

### 3. analyzer/samples.py:82 — コメントに「the API in the same container」が残っている

- 指示の `rg` は `-e コンテナ` で英語の `container` を拾わないので漏れた。`rg -n -i container --glob '!archives/**'` で見つかるのはここだけ。
  今は「API の子プロセス」（docs/raspi.md:140 の書き方）。

### 4. bganalyzer.service:6 — `After=network-online.target` はユーザー unit では何もしない

- 実測: `systemctl --user list-units --all 'network-online*'` → `0 loaded units listed.`。network-online.target はシステムの
  マネージャーにしかなく、ユーザーのマネージャーからは順序を付けられない。`0.0.0.0` に bind するだけなので、ネットワークを待つ必要もない。
- 害は無いが、「ネットワークを待っている」と読める。消してよい（作り込みすぎの節にも書いた）。

### 5. docs/PI_CHECKS.md:13 と PI-040 の順番

- 「Pi の上の Claude Code がやること」の 1. は `systemctl --user restart bganalyzer` で、PI-040 を済ませる前には
  `Unit bganalyzer.service not found` で落ちる（unit がまだ入っていないため。未確認だが systemd の普通の挙動）。
  Pi の Claude Code は 1. から順に進めるので、PI-040 を先にやる旨が無いと、最初の一歩で止まって報告が返ってくる見込み。
  PI-040 の冒頭か 1. に「PI-040 が残っているあいだは PI-040 から」と一言あると止まらない。

### 6. docs/PI_CHECKS.md:92-107（PI-040）の抜け

点検した結果、頼まれた 3 点は押さえてある:
- コンテナの止め方: 名前 `bganalyzer-app-1` とイメージ名 `bganalyzer` はこの Pi の `docker ps` と一致（`bganalyzer-app-1 bganalyzer 0.0.0.0:8000->8000/tcp`）。
  `docker rm -f` で消すので `restart: unless-stopped` で戻ってくることもない。
- ポート 8000: コンテナを消してから `enable --now` する順番で、ぶつからない。
- root 所有の `collected/`: `sudo chown -R` で直している。
- linger: この Pi は今 `Linger=no`（実測）なので、`enable-linger` の行は要る。

残る小さな抜け:
- compose が作ったネットワーク `bganalyzer_default` が残る（未確認。compose の既定の名前）。後片付けに `docker network rm bganalyzer_default` を足すかどうか。
- `uv sync --frozen` で dev の依存（pytest など）も Pi に入る。Docker は `--no-dev` だった。CI も同じ入れ方なので食い違いは無く、害も無い。報告だけ。

## 問題なし

- `bganalyzer.service` の書き方: `sed` で置き換えたものを `systemd-analyze --user verify` → 警告なし（rc=0）。
- `WantedBy=default.target`・linger 前提・`Restart=always` + `RestartSec=5`（起動回数の上限に当たりにくい）: ユーザー unit として正しい。`--reload` なし・`--workers 1` で CLAUDE.md どおり。
- `sys.executable`: `.venv/bin/uvicorn` の shebang は `#!/home/ytani/work/bganalyzer/.venv/bin/python`、その python の `sys.executable` は `.venv/bin/python`（実測）。測り直しの子プロセスは venv の python になる。
- ログ: この Pi は `/var/log/journal` があり（永続）、`journalctl --user` が使える。
- `gnubg` が使う OS のライブラリ（libglib2.0-0・libreadline8・libgmp10）はこの Pi に入っている（`dpkg -l`）。新しく入れた Pi OS Lite で揃っているかは未確認（Docker のときは Dockerfile が apt で入れていた）。
- test.yml: docker.yml の確認（/health 待ち・/analyze・/analyze-photo・`/`・/version と commit）を全部引き継いでいる。matrix は `ubuntu-latest` と `ubuntu-24.04-arm` で両方走る。トリガーは全 PR で docker.yml より広い。落ちたのは `workflow_dispatch` だけ。
- tools/pi_ui_check.py: `evaluate()` は以前の `docker compose exec ... python recognizer/evaluate.py` と同じ（cwd もリポジトリ）。`sys.executable` ではなく `.venv/bin/python` にしたのは、`uv run --no-project --with playwright` の python に numpy/cv2 が無いので正しい。後片付けは `rm -f` と同じ。ただし `collected/` が root 所有のままだと `unlink` が PermissionError で落ちる（以前は黙って無視）。PI-040 の chown を済ませれば起きない。
- バージョン: analyzer・recognizer の変更は docstring とコメントだけ、tools/ は対象外。CLAUDE.md の「バージョン」どおり上げなくてよい。
- README.md・CLAUDE.md・analyzer/README.md・docs/HANDOVER.md の手順は unit と食い違っていない。
- 残っている Docker の記述は、TODO.md・gnubg-wheel.yml（ビルド用）・PI-040（切り替え手順）・HANDOVER.md と CLAUDE.md の「使わない」だけで、意図どおり。
- 範囲: docs/PI_CHECKS.md:28 の「Pi では `uv sync` が gnubg で落ちるため」を消したのは TODO-055 で古くなった記述の片付けで、Docker と同じ段落なので許容範囲。

## 作り込みすぎ

- `bganalyzer.service:6`: delete: `After=network-online.target`。ユーザーのマネージャーには無い unit（実測）。何も置かない。（検討）
- `docs/raspi.md:49`: shrink: `mkdir -p ~/.config/systemd/user collected` の `collected`。`analyzer/samples.py:63` が保存のときに `mkdir(parents=True)` する。`mkdir -p ~/.config/systemd/user` だけでよい。（好みの範囲）

net: -1 lines possible.
