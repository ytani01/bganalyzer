# TODO-086 の分担

| 担当 | 何を | 理由 |
|---|---|---|
| main | 洗い出し・案・仕様（この README） | 案はユーザーと決めるため |
| implementer（Opus 5.5 / medium） | 下の仕様の実装 | index.html・style.css・app.js・board-view.js にまたがる |
| reviewer（Opus 5.5 / high） | 差分のレビュー | 画面の並びと、タップの扱いが変わる |
| verifier（Sonnet 5.5 / medium） | Playwright で実測 | 素材と突き合わせる対象が 10 を超えるので Haiku にしない |

撮影と計測は `shots.py`（390×844、`uv run -q --no-project --with playwright python archives/agents/TODO-086/shots.py <出力先>`）。
各画面の全体（`*-full.png`）・最初の 1 画面分（`*-top.png`）と、ボタンの大きさ・位置（`*.json`）を出す。

## 洗い出し（v0.51.0、390×844）

- ボタンの高さは 24〜38px で、どの画面でも全部 44px 未満
- 「盤面を読み取る」「解析する」はヘッダーの右上で、親指から遠い
- ヘッダーが約 107px を常に取る（ゲームの種類の選択を含む）
- 四隅: 写真の高さは 180px ほど（ルーペは既にある）。下にボタン 6 個と選択 2 つ
- 盤面: 縦 1743px（画面 2 つ半）。1 ポイントの幅は約 13px で、高さを狙ってタップしにくい
- 解析結果: 1155px で、問題は小さい

## 決めたこと（2026-10-17 ユーザー）

- 案 A: 主のボタンを画面の下に固定し、ボタンはすべて 44px 以上にする。使うことが少ないものは「その他」に畳む。ゲームの種類はヘッダーから盤面の画面の設定へ移す
- 駒の編集は今のまま（タップと長押し）にし、盤にもルーペを付ける

## 仕様（implementer へ）

### 1. 下の操作バー

- `#recognize`・`#analyze`・`#speak` と `#hdr-reuse`（中の `#to-board` ごと）をヘッダーから出し、`</main>` の後に置く 1 つのバー（`position: fixed; bottom: 0`、`env(safe-area-inset-bottom)` を足す）へ移す。**id は変えない**（`app.js`・`tools/ui_snapshot.py`・`tools/pi_ui_check.py` が使う）
- 主のボタンはバーの幅いっぱい、高さ 48px 以上。`#hdr-reuse` は主のボタンの上に置く
- 中のボタンが全部 `hidden` のときはバーを出さない（写真の選択の画面）。`main` の下の余白はバーに隠れない分だけ取る
- 画面の幅が広いとき（`min-width: 1000px` など）もバーのままでよい

### 2. ヘッダー

- `#match`（ゲームの種類とスコア）をヘッダーから出し、盤面の画面の「解析の設定」の先頭に `.opt` の 1 行として置く（ラベルは「ゲーム」）。id は変えない。解析結果の画面では直せなくなる（直すときは戻る）
- ヘッダーに残るのは、アプリ名と版の行、戻る・題名の行、`#steps`（スマホでは今も出ない）だけ
- `--hdr-h`（盤を貼り付ける高さ）は `app.js` が測っているので、そのまま効くか確かめる

### 3. 押せる大きさ

- 押せるものは高さ 44px 以上: `.button`（`.small` も）、`.seg button`、`.paint-side button`、`.act`、`.back`、`select`、`.palette-counts button`、`.palette-head button`、`.history-list .del`、チェックボックスの `label`（行ごと押せるようにする）
- 文字の大きさは 15px 以上を目安に。盤の SVG の中の文字は変えない

### 4. 「その他」に畳む（`<details>`）

- 四隅の画面: `#edit-start`・`#find-again`・`#claude-corners`（と `#claude-note`）を「その他」に入れる。`#corner-reset`、`#keep-corners`、手前のホーム、手前の駒の色はそのまま見せる
- 盤面の画面: `#swap-colours`・`#reset-start`・`#export-sample`、読みの深さ（と注記）、精度の改善（`#collect-opt`・`#collect-note`）を「その他の設定」に入れる。手前のホーム・`#home-note`・`#counts`・振った人・ダイス・キューブはそのまま見せる
- 開いた・閉じたは覚えなくてよい（閉じた状態で始まる）
- `app.js` が `hidden` を切り替える要素は、中へ移しても動き方を変えない

### 5. 盤のルーペ

- `board-view.js` の `bindTap` で、指を置いた（`pointerdown`、マウスの右クリックは除く）ら、指の周りを拡大して指の上（上に場所が無ければ下）に出し、`cancel`・`pointerup`・長押しで消す
- 作り方の目安: その時の SVG を `cloneNode(true)` して、`viewBox` を指の位置を中心にした小さな範囲（3 倍ほど）にし、`position: fixed` の枠（120px 前後）に入れる。中心に印を付ける。指は動かないので追いかけなくてよい（動けばスクロールとして取り消される）
- タップ・長押し・スクロールの今の動きは変えない。解析結果の盤（`#result-svg`、押せない）には出ない

### 6. その他

- analyzer の版を 0.52.0 に（`analyzer/app.py` の `__version__`、`analyzer/static/app.js` の `APP_VERSION`）。`sw.js` の `CACHE` も 1 つ上げる
- 新しい色は `:root` の変数を使い、ダークモードでも読めるようにする
- テスト: `analyzer/test_pwa.py` だけを `uv run pytest analyzer/test_pwa.py` で流す（全体は CI）
- 報告は `archives/agents/TODO-086/implementer-report.md` に、変更点・確かめたこと・残る懸念だけ。返事は「終わったか・報告のパス・判断が要る点」だけ
