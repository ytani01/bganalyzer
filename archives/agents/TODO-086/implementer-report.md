# TODO-086 implementer の報告

仕様 1〜9 は済み（9 は管理者の判断 (b)「描かれた色で呼ぶ」で実装。末尾の節）。コミットはしていない。

## 変更点

- `analyzer/static/index.html`
  - :251 下の操作バー `#actbar`（`#hdr-reuse`（`#to-board`）・`#recognize`・`#analyze`・`#speak`。id はそのまま）。ヘッダーには brand・戻る・題名・`#steps` だけが残る
  - :172 `#match` を「解析の設定」の先頭の `.opt`（ラベル「ゲーム」）へ移した
  - :110 四隅の「その他」（`#edit-start`・`#find-again`・`#claude-corners`・`#claude-note`）。:213 盤面の「その他の設定」（`#swap-colours`・`#reset-start`・`#export-sample`・読みの深さと注記・`#collect-opt`・`#collect-note`）
  - :188 ダイスの行に `id="dice-row"` を付けた。文章は下の表
- `analyzer/static/style.css`
  - :71 `.actbar`（fixed・bottom 0・safe-area。`:has` で、中が全部 hidden のときは出さない）。`.act` を主ボタン（幅いっぱい・min-height 48px）に。`main` の下の余白は `var(--bar-h)` 足す
  - 44px: `.button`・`.back`・`header .bar`・`.paint-side button`・`.palette-counts button`・`.palette-head button`・`.history-list .del`・`select`・チェックボックスの label（:293〜）。`.button.small` と `.paint-side` の文字は 15px
  - :299 `details.more`（summary が 44px）。:306 `.loupe`
  - 使わなくなった `header .actions`・`.bar2`・`header .match`・`#to-board` の margin・`.opt .dice + .note` を消した
- `analyzer/static/app.js`
  - :14 `APP_VERSION` 0.52.0。:1139 `--bar-h` を ResizeObserver で測る（`--hdr-h` と同じやり方）
  - :83〜 `diceIn`（入れたダイス）・`cubeOffered`（キューブが片側にあって `offered`）を足し、`rolled` はダブルされたところでは null にした。履歴と精度改善用の書き出しは今までどおり入れたダイス（`diceIn`）を残す
  - :300 ダブルされたところでは `#dice-row` と `#dice-note` を出さない
  - :828 写真の読み取りでダイスがあり、キューブが片側で offered のときは offered を外す（サーバーは「ダイスがあれば持っているキューブ」として解析しているため。外さないと、写真にキューブとダイスがあると結果が古い扱いになり、PI-017 の場面も崩れる）
  - :330 `#cube-help` は、ダイスがあるときは空にして隠す。:240 `#counts` の注記は上がった駒があるときだけ。:251 `#home-note` は左右の推測が怪しいときだけ
- `analyzer/static/board-view.js` :139, :161〜 ルーペ（`pointerdown` で出し、`cancel`（pointerup・pointercancel・pointerleave・長押し・右クリック）で消す）。`#result-svg` は `pointer-events: none` なので出ない
- `analyzer/static/result.js` 表と重なる文を消した（下の表）。ダイスもキューブも無く終局でもないときだけ「次に振るのは〜」を残す
- `analyzer/app.py` `__version__` 0.52.0。`analyzer/static/sw.js` `CACHE` v56
- `analyzer/test_pwa.py` `#match` の場所の検査を盤面の画面へ（`test_match_is_in_the_board_settings_and_sent`）。結果の HTML の検査を「ピップ リード」「振ったのは」が出ないことへ
- `tools/pi_ui_check.py` :74 PI-017 の確認が古い `#cube-help` の文を待っていたので、空を待つようにした（範囲外のファイルだが、文言に頼っていたので合わせた）

## 文章の前 → 後

| 場所 | 前 | 後 |
|---|---|---|
| 写真の選択の冒頭 | 盤の写真を撮るか、アプリの画面のスクリーンショットを選んでください。写真なしで手で入力することもできます。 | なし |
| コツ | 開いた状態で始まる | 閉じた状態で始まる |
| 手で入力の小さい字 | 写真なし／初期配置から | 初期配置から |
| 最近の写真の注記 | 選ぶと、盤面を読み取る前の四隅の画面から始まります（…黄色いボタンで開けます）。最近の 10 枚まで、この端末の中だけに残します。 | 最近の 10 枚を、この端末の中だけに残します。 |
| `#corner-help`（合わせる） | 点をドラッグして、盤の遊戯面（枠の内側）の四隅 1 左上・2 右上・3 右下・4 左下（手前に座った向き）に合わせてください。 | 点をドラッグして、枠の内側の四隅（手前から見て 1 左上・2 右上・3 右下・4 左下）に合わせてください。 |
| `#corner-help`（見つからない） | 盤を自動で見つけられませんでした。／見つかりませんでした。＋上の文＋盤が小さいときは「画像を編集」で…「もう一度検出」で探し直せます。 | 盤を見つけられませんでした。＋上の文＋盤が小さいときは「その他」の「画像を編集」で切り抜いてください。 |
| `#corner-help`（見つけた） | 盤の四隅を自動で置きました。ずれていたら＋上の文 | 上の文だけ |
| `#corner-help`（探し中） | 盤の四隅を探しています… ＋上の文 | 盤の四隅を探しています… |
| `#corner-help`（タップ） | 手前に座った向きで、盤の遊戯面（枠の内側）の四隅を **n. 〜** の順にタップしてください（左上→右上→右下→左下）。 | 枠の内側の四隅を、手前から見て **n. 〜** の順にタップしてください。 |
| `#corner-help`（編集） | 写真の向きをボタンとスライダーで直し、…「確定」を押すと、その画像で四隅を探し直します。 | 向きを直し、盤のまわりを斜めにドラッグして囲んでください。 |
| `#corner-help`（決まった） | 四隅が決まりました。ホーム側と駒の色を選んで上の「盤面を読み取る」を押してください。 | 「合わせる」の文 |
| 四隅をやり直すの横 | 点はドラッグで動かせます。 | なし |
| `#keep-corners` の注記 | 読み取りで四隅を枠に合わせ直さない。点を動かすと入ります。ざっくり合わせたときは外してください | オンだと読み取りで四隅を合わせ直さない（ざっくり置いたときは外す） |
| `#claude-note` | 押すと写真が Anthropic に送られます | 写真が Anthropic に送られます |
| `#editor-title` | タップ: その段まで置く／一番上の駒で 1 個減る／番号で空に。長押し: 色と数を選ぶ（下が手前） | タップした段まで置く（一番上なら 1 個減る）・番号で空に・長押しで色と数（下が手前） |
| `#counts` の注記 | 上がった駒は 15 − 盤上 − バー として数えます。読み取りで駒を見落とすと、その分が上がった扱いになります。（いつも） | 上がりは 15 − 盤上 − バー で数えます。（上がった駒があるときだけ） |
| `#errors`（上がり） | 上がった駒が 手前 x 個・奥 y 個 の扱いです。駒の見落としがないか確かめてください。 | 上がりが 手前 x 個・奥 y 個になっています。駒の見落としがないか確かめてください。 |
| `#home-note` | 手前の人のホームボードは〜です。／駒の並びから〜と推測しました。逆なら… | 推測が怪しいときだけ: ホームの左右を決められず、〜にしました。違えば選び直してください。 |
| ダイスの行 | 入れると最善手も出します | なし |
| `#dice-note` | 写真からダイスの目を読み取りました。違うときは直してください。 | 写真から読み取った目です。違えば直してください。 |
| `#cube-note` | 写真からキューブを読み取りました。違うときは直してください。 | 写真から読み取ったキューブです。違えば直してください。 |
| `#cube-help`（ダイスあり） | ダイスがあるので、最善手を出します。 | なし（隠す） |
| `#cube-help`（ダブル） | X の人が n にダブルしたところとして、Y の人がテイクかパスかを判定します。 | Y の人のテイク／パスを判定します。 |
| `#cube-help`（持っていない） | キューブは Y の人が持っているので、X の人はダブルできません。 | キューブは Y の人のもの。X の人はダブルできません。 |
| `#cube-help`（ダブルするか） | ダイスが無いので、X の人がダブルすべきかを判定します。 | X の人のダブルを判定します。 |
| 読みの深さの注記 | 3手は少し正確になりますが、10倍以上時間がかかります。 | 3手は 10 倍以上かかります。 |
| `#collect-note` | 「Pi に残す」にすると、解析するたびに写真と直した後の盤面をサーバー（Pi）に保存し、読み取りの改善に使います。 | 「Pi に残す」だと、解析のたびに写真と盤面を Pi に保存します。 |
| 結果（キューブあり） | 〜が n ピップ リード。 | なし |
| 結果（ダイスあり） | 〜が n ピップ リード。振ったのは〜の人。 | なし |
| 結果（ダイスもキューブも無し） | 〜が n ピップ リード。次に振るのは〜の人。 | 次に振るのは〜の人。 |
| 結果・最善手の注記 | 番号は〜の人から見たポイント番号です。盤面図の矢印は選んだ手です（行をタップで切り替え）。 | 番号は〜の人から見たもの。行をタップで矢印を切り替え。 |
| 結果・末尾の注記 | gnubg n手読み。勝率とエクイティはキューブなし、キューブの判断は〜。 | gnubg n手読み・勝率とエクイティはキューブなし・キューブの判断は〜。 |

読み上げ（`speechText`）は変えていない。写真の「保存しません」の注記はそのまま。

## 7. 出し分けたもの

- `#dice-row`・`#dice-note`: ダブルされたところ（キューブが片側・`#cube-offered` オン）では出さない。そのときのダイスは `rolled()` が null を返すので、解析・盤面図・`inputsKey` に効かない（Playwright で `BgApp.rolled()` が null、チェックを外すと `[3, 1]` に戻るのを確かめた）
- `#cube-help`: ダイスがあるときは出さない
- `#counts` の注記: 上がった駒があるときだけ
- `#home-note`: 左右の推測が怪しい（margin < 1）ときだけ。推測が確かなとき・決まっているときは、「手前のホーム」の選択が見えているので出さない
- ほかに意味の無い行は見つからなかった（`#cube-side`・`#match-score`・`#collect-opt` などはそのまま）

## 確かめたこと

- `uv run pytest analyzer/test_pwa.py`: 21 passed、終了コード 0（警告 1 件は starlette の DeprecationWarning で、前からある）
- `shots.py`（390×844）:

  | 画面 | ページの高さ | 44px 未満 |
  |---|---|---|
  | 1 写真の選択 | 844px | 0 |
  | 2 四隅 | 844px | 1（`#keep-corners` のチェックボックスの input 自体。20×20。行の label は 44px で押せる） |
  | 3 盤面 | 1517px（前 1743px） | 0 |
  | 4 解析結果 | 1146px（前 1155px） | 0 |

  `shots.py` そのままだと、四隅は「写真を読み込んでいます…」の待ちの間に撮られる（`cornerGuess` だけを待つため）。`#corners` が出て `#busy` が消えるまで待つ版をスクラッチで流して、上の数と画像を確かめた（数は同じ）。verifier が使うときは待ち方を直した方がよい
- Playwright（手で入力 → 盤面）: 写真の選択の画面ではバーが `display: none`、盤面の画面で `--bar-h` 65px。点を押すとルーペ（120px、指の上、上に余地が無ければ下）が出て、離すと消え、タップも効く（元に戻すが押せるようになる）。長押しでルーペが消えてパレットが出る
- 画像はスクラッチの `shots2/`・`shots3/`・`loupe.png` に残した

## 判断が要る点（1 回目。管理者の判断済み）

1. **9（「白」「黒」）は手を付けていない。**（→ (b) に決まった） `white`（手前）の駒は `bottomColour` で暗くも明るくもなる（既定は 1 = 明るい方）。「暗い方」を選ぶと、手前の駒は黒く描かれるのに「白」と呼ぶことになり、パレットや「空の所に置く色」のボタンでは黒い丸の横に「白」と出る。どちらにするか決めてほしい:
   - (a) 内部の `white` をいつも「白」と呼ぶ（機械的に置き換えるだけ。「暗い方」のときは食い違う）
   - (b) 描かれた色で呼ぶ（`bottomColour` で名前を入れ替える。サーバーの `summary`（`analysis.py`）の「手前が有利」も直すなら、`/analyze` に駒の色を渡す必要がある）
   - なお、結果の `<h2>` に出るのはサーバーの `summary`（「奥が有利: 勝率…、ピップ 手前 167 / 奥 160」）で、どちらの案でも `analysis.py` と `test_api.py` まで変わる
2. （→ このままでよいと決まった）ダブルされたところでダイスを効かせなくしたため、**キューブを片側に置くと（`offered` が既定でオン）入れたダイスが隠れ、解析はテイク／パスになる。** 今までは「ダイスがあれば最善手」だった。持っているキューブでダイスを振った局面は、「ダブルされたところ」のチェックを外す必要がある。写真から読んだときだけは、ダイスがあれば自動で外す（上の :828）

## 残る懸念

- `#corner-help` の min-height（スマホで 3em）はそのまま。文が短くなったので 1〜2 行分の空きが出る場面がある
- サーバーの `summary` は表と重なる（ピップ）が、8 の範囲（`result.js`）の外なので変えていない
- ルーペは 3 倍で、1 ポイント半ほどしか映らない。狭く感じるなら `LOUPE.zoom` を 2〜2.5 に

## 9. プレイヤーの呼び方（白・黒、描かれた色で呼ぶ）

### 変更点

- `analyzer/analysis.py:21` `names_ja(white_light)`（明るい方が「白」）。`summary_ja`・`cube_summary_ja`・`match_ja` は `name` を引数で受ける（既定は white＝白）。ピップの「手前 / 奥」も名前にした
- `analyzer/models.py:35` `AnalyzeRequest.bottom_colour`（1: 手前が明るい方、0: 暗い方、省略: white＝白）
- `analyzer/app.py` `_run` が `bottom_colour` で名前を選ぶ（:83）。`/analyze` はリクエストの値を、`/analyze-photo` はフォームの `bottom_colour` を渡す。`/analyze-photo` の `bottom_colour` は省略できるようにし（`None`）、読み取りには今までどおり `0` を渡す。省略したときの名前は white＝白
- `analyzer/static/result.js:10` `NAME` を白／黒にし、`setNames(bottomColour)` で入れ替える。`matchText`・勝率の帯・表の見出しも `NAME` で書く。読み上げも同じ `NAME`
- `analyzer/static/board.js` `errors(b, name)`（既定は白／黒）
- `analyzer/static/app.js:169` 手前の駒の色の part で `setNames` を呼び、`.nm-white`・`.nm-black` の文字を書き換える。駒の数・上がりの警告・キューブの説明・結果の part は `bottomColour` が変わったら描き直す。`inputsKey` に `bottomColour` を足した（サーバーの summary の名前が変わるので、色を変えると結果は古い扱い）。`/analyze` に `bottom_colour` を送る
- `analyzer/static/index.html` プレイヤーを指す「手前」「奥」を `<span class="nm-white">白</span>`・`<span class="nm-black">黒</span>` にした（パレット・置く色・盤面の画面のホーム・スコア・振った人・キューブ）。中に名前があるので、置く色とスコアの `aria-label` を外した
- `analyzer/static/style.css:314` 名前の span は `pointer-events: none`（`.seg` のクリックは `e.target.dataset.value` を読むため）
- `analyzer/test_api.py`・`analyzer/test_pwa.py` 文言を白／黒に。`bottom_colour: 0` で「黒が有利」「ピップ 黒 167 / 白 167」になる検査と、`setNames(0)` で読み上げ・表・マッチの文が入れ替わる検査（`test_names_follow_the_colour`）を足した
- 変えていない: 四隅の画面の「手前のホーム」「手前の駒の色」、`#corner-help` の「手前から見て」、`#editor-title` の「（下が手前）」（写真や盤の向きのことなので）。コメントと内部の `white`・`black`

### 前 → 後（9 の分。X は 手前が明るい方なら 白、暗い方なら 黒。Y はその逆）

| 場所 | 前 | 後 |
|---|---|---|
| パレット・空の所に置く色 | 手前 / 奥 | X / Y |
| 盤面の画面のホーム | 手前のホーム | X のホーム |
| スコア | 手前 n・奥 m | X n・Y m |
| 振った人・次に振る人、キューブの場所 | 手前 / 奥 | X / Y |
| `#counts` | 手前: 盤上とバー…／奥: … | X: …／Y: … |
| 上がりの警告 | 上がりが 手前 x 個・奥 y 個… | 上がりが X x 個・Y y 個… |
| 駒が多すぎる（board.js） | 手前の駒が n 個あります（15個まで） | X の駒が n 個あります（15個まで） |
| `#cube-help` | 手前の人／奥の人 | X の人／Y の人 |
| 結果の勝率の帯・表の見出し | 手前 / 奥 | X / Y |
| 結果の文・最善手の見出し・注記・読み上げ | 手前の人／奥の人 | X の人／Y の人 |
| マッチの文（画面・読み上げ） | 7 ポイントマッチ 手前 3 対 奥 5 | 7 ポイントマッチ X 3 対 Y 5 |
| サーバーの summary | 手前が有利: …、ピップ 手前 167 / 奥 160 | X が有利: …、ピップ X 167 / Y 160 |
| サーバーのキューブの文 | 手前はダブルすべき、奥はテイク など | X はダブルすべき、Y はテイク など |

### 確かめたこと（9 と追加の直し）

- `uv run pytest analyzer/test_pwa.py`: 22 passed、終了コード 0
- `uv run pytest analyzer/test_api.py`: 46 passed、終了コード 0（警告 1 件は前からある starlette のもの）
- Playwright（ローカル、公開サンプル、390×844）: 明るい方のとき、振った人・置く色が「白,黒」、`#counts` が「白: …」、summary が「黒が有利: …、ピップ 白 167 / 黒 160」。`bottomColour` を 0 にすると「黒,白」「黒: …」になり、結果は古い扱いになる。解析し直すと summary は「白が有利: …、ピップ 黒 167 / 白 160」。名前の span をタップしても、ボタンの値で手番が変わる
- `shots.py` の待つ条件を直した（`#corners` が出て `#busy` が消えるまで待つ）。直した後の 4 画面の数は前の表と同じ（844・844・1517・1146px、44px 未満は 0・1・0・0）

### 追加の直し（9 の確かめの途中で見つけた）

- `analyzer/static/style.css:122` `html { scroll-padding-bottom: var(--bar-h) }`。Playwright が行をスクロールで画面に入れても、下のバーの裏に隠れて押せなかった（入力欄にフォーカスしたときも同じことが起きうる）

### 残る懸念（9 の分）

- `analyzer/README.md` には「手前／奥」と、ヘッダーの「盤面を読み取る」「解析する」・マッチの欄の記述が残っている（:48・:52〜:73）。文書は担当外なので直していない
- `/analyze` の `bottom_colour` と、`/analyze-photo` で省略できるようにしたことは、API の説明（README など）に書かれていない
- 前に決めた `bottomColour`（写真の履歴に残したもの）がそのまま使われるので、履歴から開いた写真の名前も、その写真の設定で決まる
- `shots.py` の計測では、閉じた `<details>` の中のボタン（`#edit-start` など）も数に入っている（大きさは 0 ではないと出る）。44px 未満の数には影響しない

## 文書を今の実装に合わせた（管理者の依頼）

対象は `rg -n -e '手前' -e '奥' -e 'ヘッダー' -e 'マッチ' README.md analyzer/README.md docs/raspi.md docs/HANDOVER.md`。直す箇所があったのは `analyzer/README.md` だけ（`README.md`・`docs/raspi.md`・`docs/HANDOVER.md` には、画面の並び・文言・API に関わるものが無かった）。

- `analyzer/README.md:37-40` 「画面の並び（TODO-086）」の段落を足した（下のバー、44px、「その他」、白・黒の呼び方と、写真の向きを言う所は「手前」のまま）
- `analyzer/README.md:42` 「うまく読み取るコツ」は閉じてあるので「必要なら開いて読み」に
- `analyzer/README.md:46` 「画像を編集」「もう一度検出」「Claude に選ばせる」は「その他」の中にある、と足した
- `analyzer/README.md:54` 「ヘッダーの「盤面を読み取る」」→「画面の下の「盤面を読み取る」」
- `analyzer/README.md:59-60` ルーペの行を足し、長押しの吹き出しの「手前／奥」→「白／黒」
- `analyzer/README.md:62-64` ホームの切り替えは画面では「白のホーム」か「黒のホーム」。「その他の設定」に畳んだもの。ホームの注記は左右を決められなかったときだけ
- `analyzer/README.md:65` ダイスの注記の文言を新しい文に
- `analyzer/README.md:67` 読みの深さは「その他の設定」の中。「ヘッダーの「解析する」」→「画面の下の「解析する」」
- `analyzer/README.md:69-70` キューブの場所「中央 / 手前 / 奥」→「中央 / 白 / 黒」。キューブの注記の文言を新しい文に
- `analyzer/README.md:72` ダブルされたところではダイスの欄を出さず、解析にも使わない。写真からダイスが読めたときはチェックを外す、を足した
- `analyzer/README.md:74-76` マッチは盤面の画面の「解析の設定」の先頭の「ゲーム」（結果の画面では変えられない）。「手前と奥のスコア」→「白と黒のスコア」。「結果の画面で変えると解析し直す」を消した
- `analyzer/README.md:82` 「ヘッダーの「読み上げ」」→「画面の下の「読み上げ」」。読み上げの例を「7 ポイントマッチ 白 3 対 黒 5です。」に
- `analyzer/README.md` `/analyze` の表に `bottom_colour` の行を足した。応答の例の `summary` と、マッチの `summary` の例を白・黒に
- `analyzer/README.md` `/analyze-photo` の `bottom_colour` は省略できる（省略すると読み取りには 0、summary では white が「白」）、と足した
- 変えていない: `analyzer/README.md:130` の色の呼び方（white = 手前）、盤の上の場所を言う「手前は盤の下、奥は盤の上」「バーは上半分が手前」「手前側から見たポイント」、「ヘッダーの戻る」（戻るはヘッダーに残っている）
- 担当の定義では文書は担当外だが、管理者の依頼で直した

## レビューを受けて直したこと

- 要修正 1: `tools/pi_ui_check.py` に `reveal(page, selector)` を足し（閉じた `<details>` の summary を押して開く）、`#export-sample` と `collect` の seg を押す前に呼ぶ。`tools/ui_snapshot.py` は `Run.reveal` を足し、`click`・`seg`（`go` も `click` を通る）の前に開く。記録の形（SNAP）は変えていない
- 要修正 1 の続き: `tools/ui_snapshot.py` の manual の流れで、キューブを片側に置いた後にダイスを選んでいた所が、ダイスの欄が隠れるので止まっていた。人の操作と同じく「ダブルされたところ」を外してからダイスを消し、また入れる形にした（スナップショットの名前が 1 つ増え、1 つ変わる）
- 要修正 2: `analyzer/static/app.js` の `CRAWFORD_CUBE` を「…「ゲーム」のクロフォードを外してください。」に
- 要修正 3: `docs/raspi.md` の `double`（キューブの説明は出ない）、`collect`（盤面の画面の「その他の設定」の「精度の改善」）、「精度改善用に集めた写真」の節の冒頭（同じ場所）を今の画面に合わせた。`tools/pi_ui_check.py` の collect のコメントも同じ
- 指摘 4: `analyzer/app.py` の `/analyze-photo` の `bottom_colour` を `Form(0)` に戻し、`or 0` を消した（省略したときは読み取りも名前も 0）。`analyzer/README.md` の /analyze-photo の説明も合わせた
- 指摘 5: 「その他の設定」の summary に、既定と違う値を添える（`index.html` の `#more-set`、`app.js` の `drawMoreSet`）。3手なら「3手」、「Pi に残す」はサーバーが写真を残せるとき（`#collect-opt` が出ているとき）だけ。版を取った後に描き直す
- 指摘 8: `analyzer/static/board-view.js` ルーペは `pointerdown` から `LOUPE_MS`（100ms）待って出す。その間に SLOP を超えて動けば `cancel` がタイマーを消すので出ない

### 確かめたこと

- `uv run pytest analyzer/test_pwa.py`: 22 passed（終了コード 0）。`uv run pytest analyzer/test_api.py`: 46 passed（終了コード 0）
- `tools/pi_ui_check.py export collect double`: 3 つとも OK（collect は off で増えず、on で 1 組でき、evaluate で 24/24。作った組は消えた）
- `tools/ui_snapshot.py record`（3 つの流れ）: 60 スナップショット、終了コード 0
- Playwright: 指を置いたままなら 150ms 後にルーペが出て、離すと消える。30ms 後に 20px 動かすと出ない。summary は既定で「その他の設定」、3手と「Pi に残す」にすると「その他の設定（3手・Pi に残す）」、戻すと元の文

### 直していないもの

- 指摘 6（結果の画面でマッチを直したときの `analyze()` が届かない）、7（新しい規則のテスト）、9（`.seg` を `closest("button")` で読む）は、依頼に無かったので手を付けていない

## レビューの 6・7 を直したこと

- 6: `analyzer/static/app.js` の `setMatch` から、呼ばれなくなった `if (state.step === "outcome") analyze();` とコメントの該当部分を消した。`analyzer/test_pwa.py` の対応する検査も消した
- 7: 規則を `analyzer/static/cube.js` の `BgCube.offered(cube)` と `BgCube.usedDice(cube, dice)` に移し、`app.js` の `cubeOffered`・`rolled` はそれを呼ぶだけにした（Node で確かめられるように）
- 7: `analyzer/test_pwa.py` に `test_no_dice_while_a_double_is_offered` を足した。ダブルされたところではダイスが null になり要求がテイク／パスになること、持っているキューブ・中央では使うこと、`rolled` が `usedDice` を通ること、ダイスの欄の出し分け、写真からダイスを読んだときに offered を外す行を見る
- 壊すと落ちるか: `usedDice` を常にダイスを返すように変えると落ちた（`assert ([3, 1] is None)`）。`rolled` を `diceIn(s)` だけにしても落ちた。どちらも元に戻し、`uv run pytest analyzer/test_pwa.py` は 23 passed（終了コード 0）
- 写真からダイスを読んだときに offered を外す規則は `recognize()` の中にあり、テストは文字列の検査だけ（動きは `tools/pi_ui_check.py double` で確かめている）
- ローカルのサービスを再起動し、Playwright で、キューブを片側（offered）に置くとダイスの欄が隠れて `rolled()` が null、チェックを外すと `[3, 1]` に戻ることを確かめた
