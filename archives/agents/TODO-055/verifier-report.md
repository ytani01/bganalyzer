# TODO-055 確認報告（verifier）

対象: branch claude/gnubg-arm64-wheel、HEAD 0866c2d、マシンは Raspberry Pi（aarch64、Linux 6.12 rpt-rpi-2712）。

## 1. uv sync --frozen

- `uv sync --frozen`: 成功、終了コード 0。出力 `Checked 27 packages in 0.26ms`
- `uv run python -c "import gnubg; print(gnubg.__file__)"`: 終了コード 0。
  `/home/ytani/work/bganalyzer/.venv/lib/python3.12/site-packages/gnubg/__init__.py`
- `direct_url.json` の中身: `{"url":"https://github.com/ytani01/bganalyzer/releases/download/gnubg-1.1.0a16/gnubg-1.1.0a16-cp312-cp312-linux_aarch64.whl","archive_info":{}}`（Release の URL）
- `uv pip show gnubg`: Version 1.1.0a16

判定: 一致。Pi で入っているのは Release の aarch64 wheel。

## 2. uv run pytest -q analyzer（--no-sync なし）

- 結果: `74 passed, 3 warnings in 225.74s (0:03:45)`。失敗 0。
- 終了コード: 記録が不完全。パイプ越しに `${PIPESTATUS[0]}` を読んだが、その表示が空だった。
  件数が `74 passed` で失敗が無いので、pytest の終了コードは 0 と読めるが、数値そのものは取れていない。
  再実行はしていない（数分かかるため）。必要なら管理者の判断で再確認。
- 警告 3 件は `starlette.testclient`（httpx の非推奨）と `multiprocessing` の fork 警告。失敗に関係しない。

## 3. docker build / 起動 / API

- `docker build -t bganalyzer-todo055 .`: 終了コード 0。
  ログに `Downloading gnubg (17.3MiB)` と `+ gnubg==1.1.0a16 (from https://github.com/ytani01/bganalyzer/releases/download/gnubg-1.1.0a16/gnubg-1.1.0a16-cp312-cp312-linux_aarch64.whl)` が出た。
  `meson` / `ninja` / `git clone` の行は無し（ソースからのビルドは無し）。
- `docker run -d --name bg055 -p 8055:8000 bganalyzer-todo055`: 起動。
- `curl -s --max-time 10 http://127.0.0.1:8055/version`:
  `{"analyzer":"0.38.1","recognizer":"0.21.0","commit":"0866c2d","samples":false}`
- `/health`: `{"ok":true}`
- `POST /analyze` (position_id 4HPwATDgc/ABMA): 成功。`plies":2`、equity white 0.076、black -0.076 などが返った（gnubg の評価）。
- `POST /analyze-photo` (samples/screen1.png、corners は screen1.truth.json から、home=left、bottom_colour=1): 成功。
  返り値のキーは `recognized, home, home_guess, errors, warnings, geometry, dice_read, cube_read, analysis`。
  `analysis` に gnubg の評価が入っていた（position_id 4HPiASHgc/ABMA、plies 2）。
- 片付け: `docker rm -f bg055` 終了コード 0、`docker rmi bganalyzer-todo055` 終了コード 0。
- 本番の compose のコンテナとポート 8000 には触れていない。

判定: 一致。

## 4. GitHub Actions

- PR: #176 `build: Pi（aarch64）でも uv sync を通す（TODO-055）` が claude/gnubg-arm64-wheel から OPEN（作成 2026-10-15 10:08:57 UTC）。PR は既にある。
- `gh run list --branch claude/gnubg-arm64-wheel -L 10` の状況（4 件とも completed / success）:
  - docker: success（4m）
  - cpu-match: success（4m）
  - test: success（4m）
  - accuracy: success（4m）

## 5. git status

- 作業ツリーは変更なし（`git status --short` は空）。確認でコード・文書は触っていない。
- 作ったのは本報告ファイルのみ（`archives/agents/TODO-055/verifier-report.md`）。

## 判断が要る点

- pytest の終了コードは数値として記録できなかった（上記 2 の注記）。件数と失敗 0 からは成功と読めるが、厳密には確かめていない。
- 残っている懸念は無し（確認の範囲では）。
