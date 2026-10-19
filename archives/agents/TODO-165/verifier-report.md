# TODO-165 verifier の報告

## 結果
期待どおり。サーバーの設定で最初の画面の文が切り替わった。

## 測り方
- worktree（`impl-165`、HEAD は b21909e）で `uv run uvicorn app:app --app-dir analyzer --port <P>` を 2 つ起動
  - 8002: `BG_SAMPLES_DIR` をスクラッチの空ディレクトリに設定
  - 8003: 設定なし
- Playwright（システムの `/usr/bin/chromium`、幅 390×844、新しいページ）で `/` を開き、
  ヘッダーの版の表示が出る（`/version` の取得が済む）のを待ってから、`evaluate` で
  `/version` の `samples` と 2 つの p の `hidden`・`display`・`textContent` をまとめて読んだ。各条件 1 回
- 終了コード 0。測定後に 4 つのプロセスを PID を確かめて kill し、ポートが空いたことを確認

## 測った値
| 条件 | `/version` の `samples` | `photo-note` hidden / display | `photo-note-keep` hidden / display |
|---|---|---|---|
| `BG_SAMPLES_DIR` あり（8002） | true | true / none | false / block |
| 設定なし（8003） | false | false / block | true / none |

表示される文字列:
- `photo-note`: 「写真はサーバーで読み取るだけで、保存しません。」（設定なしのときだけ見える）
- `photo-note-keep`: 「解析すると写真と盤面をサーバーに保存し、読み違えた写真は盤の外を黒く塗って公開のサンプルに入れることがあります。盤面の画面で「保存しない」にもできます。」（`BG_SAMPLES_DIR` ありのときだけ見える）

## 補足（実害は未確認）
- `index.html` の初期状態は `photo-note` が見え、`photo-note-keep` が `hidden`。
  設定なしの側は初期状態のままでも同じ結果になるので、この測定だけでは
  「`samples: false` のとき app.js が正しく隠す」ことまでは区別できない
  （`hidden = !serverKeepsSamples` の分岐は `samples: true` の側で効いていることを確認）。
- `/version` の取得が遅い間は、設定ありのサーバーでも一瞬 `photo-note`（保存しません）が見えうる
  （初期状態がそうなので）。今回は測っていない。判断は管理者へ。
- Playwright 同梱の chromium が入っていなかったため `/usr/bin/chromium` を使った（`tools/pi_ui_check.py` と同じ）。

## 見ていない
盤面の画面、文言の良し悪し、テストの実行、版の表示。
