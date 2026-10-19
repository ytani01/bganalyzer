# verifier 報告（TODO-161・TODO-162）

対象: worktree `impl-163`（ブランチ claude/cube-double-wording、origin/main との差分 = #480 + #481）。コードは直していない。コミットもしていない。

## 結果: 依頼の項目はすべて期待どおり（※の 1 点だけ依頼の文面と違う）

測り方: `uv run uvicorn app:app --app-dir analyzer --host 127.0.0.1 --port 8010` を起動（PID 953657、測定後に kill、残りなし）。
Playwright（headless Chromium）で evaluate。スクリプト: `/tmp/claude-649/-home-ytani-work-bganalyzer/d2126a01-abef-4ce1-a267-e5c89a1cd745/scratchpad/v.py`。

| 項目 | 測った値 | 判定 |
|---|---|---|
| 1280×800: `#steps` | `document.getElementById('steps')` = null、`nav,[data-step]` = 0 件 | 一致 |
| 390×844: `#steps` | 同上（null、0 件） | 一致 |
| `#title` が見える（両幅） | 文字列「写真の選択」、幅・高さ > 0、display/visibility も通常 | 一致 |
| 写真 1 枚（`samples/collected-app-green-far.jpg`）を選ぶ | `#title` が「写真の選択」→「四隅の調整」（1280・390 とも） | 一致 |
| キューブのボタン（bottomColour=1、既定） | white =「黒から白にダブル」、black =「白から黒にダブル」 | 一致 |
| 名前が変わる（bottomColour=0 を localStorage に入れて読み込み） | white =「白から黒にダブル」、black =「黒から白にダブル」（span が `NAME` に差し替わっている） | 一致 |
| コンソール | error・warning・pageerror とも 0 件（`errors: []`） | 一致 |
| `rg -n "#steps\|data-step" analyzer/static` | 0 件（rc=1） | 一致 |
| `/version` と版 | analyzer 0.89.3（recognizer 0.28.0）、`app.py` `__version__` = "0.89.3"、`app.js` `APP_VERSION` = "0.89.3"、ヘッダー表示「a0.89.3 · r0.28.0」 | 一致 |
| `rg -n "に対してダブル" --glob '!archives/**'` | `TODO.md` 82・85 行の 2 件が出る（旧文言を引用している項目の説明）。`--glob '!TODO.md'` を足すと 0 件 | ※ |

※ 依頼は「空であること」。コード・README・docs には残っておらず、TODO.md の項目の説明文だけ。直すかどうかは判断しない（管理者の判断）。

## 変更ファイル（origin/main との差分）

`TODO.md`、`analyzer/README.md`、`analyzer/app.py`、`analyzer/static/app.js`、`analyzer/static/index.html`、`analyzer/static/style.css`、`docs/raspi.md` の 7 つ。指示外のファイルは無い。`git status` は測定前に clean。

- `index.html`: `<nav id="steps">` を削除。キューブのボタン 2 つを `<span class="nm-black">黒</span>から<span class="nm-white">白</span>にダブル` と逆の形に（TODO の指示どおり）
- `style.css`: `#steps` の規則 5 行と狭い幅の `#steps { display: none; }` を削除。コメントの語句を 1 つ直している
- `app.js`: `STEPS` 定数と `#steps span` を更新するループ（`at` を含む）を削除。`rg -n "\bSTEPS\b" analyzer/static/app.js` は 0 件。ほかに版の更新
- `analyzer/README.md`・`docs/raspi.md`: 「に対してダブル」を新しい文言へ。README のキューブの説明に「（前者は白がダブルされた）」が足されている。意味が合っているかは読んだだけで、試してはいない
- `rg -n steps analyzer/static tools` に残るのは `moves.js`・`app.js:467-468` の gnubg の手の `steps` と `tools/ui_snapshot.py:255` のマウス移動の `steps=3` で、ヘッダーとは無関係

## 確かめられなかったこと・補足

- Playwright が要求する Chromium（1248）が入っていなかったので、入っている `/usr/bin/chromium` を `executable_path` で指定して測った。ダウンロードはしていない。
- 名前の切り替えは、画面の「色」切り替えを押さず、localStorage の `bottomColour` を先に入れて確かめた（同じ `setNames` を通る）。
- キューブのボタンは「手で入力」で盤面に入り、キューブの部品を押して数 2 を選んだ状態で読んだ。写真から読んだ場合は測っていない（同じボタン）。
- TODO.md のチェック状態・見込みの表の整合は見ていない。
- 途中で `rg` を対象のパスなしで流して標準入力待ちで止めた（こちらの手違い。自分の 2 プロセスを kill 済み）。別に PID 948309（`rg -n に対してダブル --glob !archives/**`、約 8 分経過）が同じ状態で残っている。自分のものではないので触っていない。実装担当のコマンドかもしれない。
