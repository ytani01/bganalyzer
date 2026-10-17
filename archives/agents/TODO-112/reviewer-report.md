# TODO-112 レビュー（reviewer）

対象: `git show HEAD`（1e94133、ブランチ claude/todo-112-board-settings）。コードは直していない。

消した `#more-set`・`drawMoreSet`・`#collect-note`・`details.more` の参照は、`rg -n "more-set|drawMoreSet|collect-note|details.more|\.more\b" analyzer tools` で 0 件。

## 要修正

1. **`analyzer/static/app.js:908` サーバーが samples を受けないときも `POST /samples` で写真を送る**
   - `sendSample` の条件は `state.collect !== "on" || !state.fromPhoto || !state.board || !state.historyId` だけで、サーバーの `samples` を見ていない。
     前は既定が "off" で、"on" にできるのは `#collect-opt` が出ているとき（= samples を受けるサーバー）だけだったので、実際には送られていなかった。
     既定を "on" にしたので、`BG_SAMPLES_DIR` の無いサーバー（README の `uv run uvicorn …` で立てた開発機など）で、解析のたびに写真（長辺 2048px まで）を送って 404 を受ける。
     `/version` が失敗したときも同じ（`#collect-opt` は隠れたまま送る）。
   - 実測（Playwright、ローカルホストの app、新しいページで localStorage 無し、`/samples` は route で横取りしてサーバーには届けていない、`/version` の `samples` を false に書き換え）:
     `collect: 'on'`、`#collect-opt` hidden、「解析する」で `POST /samples` が 1 回出た。samples=true のときも 1 回（こちらは意図どおり）。
     スクリプト: `/tmp/claude-649/-home-ytani-work-bganalyzer/8f84bca2-0c79-4ff5-8584-dc9dbe4ee578/scratchpad/sample_post.py`
   - サーバーは 404 で保存しないので、CLAUDE.md の「保存も外へ送ることもしない」には反しない。実害は通信量と 404 のログ（程度は未確認）。

2. **`tools/pi_ui_check.py:96`（`check_speech`）、`tools/ui_snapshot.py:191-218`（`r.go("#analyze", …)`）確認の道具が `collected/` に組を残すようになる**
   - どちらも新しいページ（localStorage 無し）で写真を読んで「解析する」を押す。既定が "on" になったので、samples を受けるサーバー（開発機の `bganalyzer.service`、Pi）に
     走らせるたび `user-<id>.*` の組が保存される。後で消すのは `check_collect`（`:160-162`）だけ。
     `collected/` は `recognizer/collected.py` の測り直しと `tune.py --collected` の材料なので、screen1 などの公開サンプルが学習用の組に混ざる。
   - 上の実測（samples=true で POST が 1 回出る）からの推定で、実サーバーに対して道具を流しての確認はしていない（書き込みになるため）。未確認。
   - live_view の窓で手で試すときも同じく保存される（それをよしとするかは判断が要る）。

## 検討

3. **`analyzer/README.md:66` 「読み取りの改善」（写真から読んだときだけ。…）が実装と違う**
   - `#export-opt` は `!s.fromPhoto` で隠れる（`app.js:260`）が、`#collect-opt` は `!v.samples` だけで決まり（`app.js:1201`）、手で並べた盤面でも出る。
     そのとき「保存する」を選んでも `sendSample` は `!state.fromPhoto` で何もしない。
     README を「サーバーに…はサーバーが受けるときだけ、ファイルに書き出すは写真から読んだときだけ」と書くか、`#collect-opt` も写真のときだけにするか。
     どちらにするかは境界線上なので報告だけ（前の版でも `#collect-opt` は fromPhoto を見ていなかった）。

4. **`analyzer/static/style.css:308` 消した `details.more` の説明コメントが残っている**
   - `/* What is used less often, folded (TODO-086). */` の下にあった規則はすべて消え、新しいコメント（`:309`）が続いている。古い 1 行は今の CSS の説明になっていない。

5. **`analyzer/samples.py:3-4` docstring 「the app sends them only when the user turns it on」が既定 "on" と食い違う**
   - 差分に含まれていない文書。TODO-112 で既定が変わったので、今は「ユーザーが切らない限り送る」。

6. **旧名が差分の外に残っている**（`rg -n "Pi に残す|駒の色を入れ替える" --glob '!archives/**'`）
   - `recognizer/README.md:229` 「アプリで「駒の色を入れ替える」を押したら」→ ボタンは「色を入れ替え」になった。今の手順の説明なので直す対象。
   - `recognizer/README.md:456`、`recognizer/collected.py:1`、`recognizer/tune.py:11,124` 「Pi に残す」→ 画面に無い名前。
     collected.py・tune.py は測る道具なので、直しても recognizer の版は上げない（CLAUDE.md「バージョン」）。
   - `samples/CREDITS.md:30` と `TODO.md:21` は過去の出来事（「集めた」「済み」）の記述なので、そのままでもよい。

## 好みの範囲

なし。

## 作り込みすぎ

- `tools/pi_ui_check.py:69-73`: delete: `reveal()`（閉じた `details` を開く）。盤面の画面に `details` が無くなり、`collect`・`export-sample` の祖先にも無い（`<details` は `index.html:53` の tips だけ）。呼んでいる `:112`・`:148` も消せる。
- `tools/ui_snapshot.py:110-116`: delete: `Recorder.reveal()` と `click()` の中のその呼び出し。同じ理由で何もしない。`click` は `self.page.click(selector)` だけになる。
- `#improve:not(:has(...))`・`#collect-opt:not([hidden]) + #export-opt` はそれぞれ要る（`:not([hidden])` を外すと、収集が隠れたとき見出しの直後に余白が出る）。

net: -10 lines possible.

## 確かめたこと（意図どおり）

- CSS（Playwright、`/usr/bin/chromium`、390×844、index.html を file:// で JS 無しに開いて hidden を切り替え。`css_check.py` 同じ scratchpad）:

  | collect-opt | export-opt | `#improve` の display | 2 つの間 |
  |---|---|---|---|
  | 隠す | 隠す | none | - |
  | 出す | 隠す | block | - |
  | 隠す | 出す | block（`#export-opt` の margin-top 0） | - |
  | 出す | 出す | block | 24px（説明の行の高さは 19.5px） |

  `:has` はこの CSS で既に使っている（`style.css:77,82,306`）ので、対応ブラウザの範囲は変わらない。
- 既定 "on": `stored()`（`app.js:25-27`）は localStorage に "off" があればそれを返すので、前に「オフ」を押した端末はそのまま。押したことが無い端末は "on"。
- 版: `analyzer/app.py` と `APP_VERSION` がともに 0.64.0。recognizer は変えていない。
- テスト: 画面の配線の変更で、pytest で見る所は無い。`collect` の切り替えは `pi_ui_check.py collect` が見る（今回は流していない）。
