# TODO-056 確認報告（verifier）

確認日: 2026-10-15、ブランチ claude/systemd-instead-of-docker（未コミット）。コードは変更していない。8000 番・Docker・systemd には触れていない（8000 番の本番アプリは動いたまま）。

## 結果まとめ

| # | 確認 | 結果 |
|---|------|------|
| 1 | test.yml の「起動して解析・写真認識を試す」を 8001 番で実行 | 通過（終了コード 0、末尾に STEP1_ALL_OK） |
| 2 | bganalyzer.service の検証と ExecStart の実在 | 通過（verify は警告なし、終了コード 0。uvicorn は実在） |
| 3 | docs/raspi.md のコマンドの引数 | 一部に食い違い（tune.py は通過。collected.py は `--help` が効かない。下記） |
| 4 | pi_ui_check.py collect（8001 番、BG_SAMPLES_DIR 付き） | **失敗**（FAIL。保存で 500 と PermissionError） |

## 1. test.yml の起動と解析・写真認識（8001 番）

実行: `bash -e` で、run の中身をポート 8001 に置き換えたものを、リポジトリのフォルダで実行（スクリプトは scratchpad の ci-run-8001.sh。`uvicorn ... --port 8001` の 1 行に `echo UVICORN_PID` を足したほかは同じ）。

- 終了コード 0。各 assert（analyze・analyze-photo・version）は通った。
- 出力の末尾: `{"analyzer":"0.39.0","recognizer":"0.21.1","commit":"c0ed76a","samples":false}STEP1_ALL_OK`
- /health は `{"ok":true}`、/ は `<html` を含む。
- 起動した uvicorn の PID は 979248。確認後に `kill 979248` で止め、`ps` で消えたことを確かめた。
- 注: 実行でリポジトリ直下に作られた analyze.json・photo.json・version.json・uvicorn.log は削除した。
- 注: `curl ... | tee` は pipefail 無しの `bash -e` と同じ扱い（GitHub の既定どおり）。

## 2. bganalyzer.service

- `sed "s|@DIR@|$PWD|g"` の結果は scratchpad の bganalyzer.service に書いた（WorkingDirectory、Environment=BG_SAMPLES_DIR、ExecStart がすべて /home/ytani/work/bganalyzer に置き換わっている）。
- `systemd-analyze --user verify <そのファイル>`: 出力なし、終了コード 0（警告なし）。
- ExecStart の `/home/ytani/work/bganalyzer/.venv/bin/uvicorn` は実在（-rwxr-xr-x）。

## 3. docs/raspi.md のコマンド（実行せず、引数の形だけ）

- `tune.py`: `--collected`、`--out` がある（`--help` は正常に出て、終了コード 0）。`--collected collected --out collected/tune.md` の形は受け付けられる。
- `collected.py`: **`--help` は効かない。** ソースは `measure(sys.argv[1], force="--force" in sys.argv)` で、argv[1] をフォルダ名として扱う。確認のために `--help` を渡したところ、フォルダ名 `--help` として扱われ `skip: 0 new pairs (measure at 10)` を出して終了コード 0。何も書かれていない（collected/ は前後で同じ）。
  - `collected --force` の形は受け付けられる（位置引数 `collected`、`--force` は argv のどこにあっても効く）。
  - 食い違いの扱い（直すかどうか）は管理者判断。`--help` を案内する文書は無い（raspi.md の表はこの形で書かれているので問題なし。`--help` は確認のために渡したもの）。

## 4. pi_ui_check.py collect（失敗）

実行:
- uvicorn を `BG_SAMPLES_DIR=/home/ytani/work/bganalyzer/collected` 付きで 8001 番に起動（health 応答あり）。
- `BG_URL=http://127.0.0.1:8001/ uv run -q --no-project --with playwright python tools/pi_ui_check.py collect`（timeout 500 秒）
- 終了コード 1。出力:

```
version: {'analyzer': '0.39.0', 'recognizer': '0.21.1', 'commit': 'c0ed76a', 'samples': True}
FAIL collect: off=[] on=[] evaluate= left=[]
```

- uvicorn のログ（scratchpad の uvicorn-step4.log）で、`POST /samples` が `500 Internal Server Error`。トレースバックの末尾:

```
PermissionError: [Errno 13] Permission denied: '/home/ytani/work/bganalyzer/collected/user-1792071413866-f47lwz.png'
```

- `stat` の結果: `collected` は `root:root drwxr-xr-x`、`collected/report.md` も `root:root`。
- 後始末: uvicorn（PID 979892）は kill して停止を確認。`collected/` は走らせる前と後で一覧が同じ（新しいファイルなし）。
- 判断: 書き込み失敗の直接の原因は、ログの PermissionError と collected/ が root 所有であることから、root 所有のディレクトリに書けなかったことだと見える（推定。chown はしていない）。失敗した保存の前に作られた一時ファイルは無い。実害（本番の Pi 側の保存）は未確認。本番の 8000 番は触っていないので影響は無い想定だが、本番の `BG_SAMPLES_DIR` が root 所有の `collected/` を指すなら、同じ失敗が本番でも起きる可能性がある（未確認）。

## 確かめられなかったこと・判断が要ること

- 4 の失敗が「collected/ の所有者の問題だけ」か、ほかの原因も混ざるかは未切り分け（境界線上の判断は報告のみ）。
- 本番（8000 番・Docker）の `BG_SAMPLES_DIR` の所有者は見ていない。
- 文書の言い回し、レイアウト、pytest、精度は見ていない（指示どおり）。
