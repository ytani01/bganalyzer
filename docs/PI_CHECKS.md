# Raspberry Pi で確かめること

**残っている項目: PI-029、PI-030、PI-031、PI-032、PI-033。** これまでに 28 件を決着させた。
新しく足すときは「完了済み」の上に節を作る（新しい番号ほど上）。**次の番号は `PI-034`。**
各項目の最初に **担当** を書く。決まりは [TODO.md](../TODO.md) と同じ（[CLAUDE.md](../CLAUDE.md) の「Raspberry Pi で確かめること」）。

マージしたあと、自宅の Raspberry Pi（公開している本番）でしか確かめられないことの一覧です。
クラウドの Claude は Pi に入れないので、**Pi の上で動く Claude Code がここを読んで確かめ、結果を書き込みます。**
外から見えること（版、画面、公開サンプルの読み取り）は、下の「クラウドから確かめられること」でクラウドからも確かめられます。

## Pi の上の Claude Code がやること

1. `bganalyzer` フォルダで `git pull` し、`docker compose up -d --build` でアプリを更新する（手順の詳細は [raspi.md](raspi.md) の「ふだんの運用」）。
2. `curl -s http://127.0.0.1:8000/version` が、pull した main の版とコミットになっているか確かめる。
3. 残っている項目の `- [ ] Pi:` を確かめ、`- [x] Pi: 日付、コミット。測った値。OK か` に書き換える。
   スマホの画面の操作は、まず Pi の上のヘッドレスのブラウザで確かめる（下の「スマホの代わりに確かめる」）。
   それでも確かめられないこと（実際の音声、iPhone の共有の画面、ファイルの添付など）だけを `- [ ] スマホ:` の行に残し、ユーザーに頼む。
4. 項目のチェックが全部付いたら、項目を `archives/pi/PI-00N. 題名.md` に移して「**日付 に完了:**」を書き足し、
   [archives/pi/index.md](../archives/pi/index.md) のいちばん上に 1 行足し、上の「残っている項目」と件数を直す。
   ユーザーがスマホで見て OK と言ったときも同じ。
5. 期待と違ったら（遅すぎる・落ちる・値が違う）、ユーザーに報告し、TODO.md に項目を足す。
6. ブランチを切って PR にし、CLAUDE.md の「共同開発」どおりにマージする（main に直接 push しない）。

## スマホの代わりに確かめる

Pi の上で、Playwright から `http://127.0.0.1:8000/` の PWA をスマホと同じ画面の大きさで操作する。
ブラウザは Pi の `/usr/bin/chromium` を使い、Playwright は `uv run --no-project` でその場で入れる
（Pi では `uv sync` が gnubg で落ちるため、pyproject.toml には入れていない）。

```bash
uv run -q --no-project --with playwright python tools/pi_ui_check.py           # 全部
uv run -q --no-project --with playwright python tools/pi_ui_check.py collect   # 名前を並べると、その確認だけ
```

1 つ失敗すると終了コードが 1 になる。どれも `samples/screen1.png`（ダイス 4-2 の写ったアプリの画面）を読み取ってから確かめる。

| 名前 | 確かめること |
|---|---|
| `double` | キューブを片側・「ダブルされたところ」にしたまま読み取っても、写真のダイスで最善手が出て、キューブの説明が「ダイスがあるので、最善手を出します。」になる |
| `speech` | 🔊 で読み上げる文が 1 つで、最善手を含み、`%`・「勝率」・「ピップ」・小数を含まない（音声は出さず、文だけを取り出す） |
| `export` | 「精度改善用に書き出す」で、写真と `.truth.json` の 2 つがダウンロードされ、盤面とダイスが画面と同じ（共有の画面が無いときの動き） |
| `export-denied` | `export` と同じことを、共有の画面がファイルを断る（`NotAllowedError`、Android の Chrome が `.json` を断るとき）ときに確かめる |
| `collect` | 「解析の設定」の下のスイッチを押して切り替える。「Pi に残す」がオフなら `collected/` が増えず、オンなら 1 組でき、`evaluate.py` で測れる。作った組はそのあと消す |

画面の操作が要る項目を足したら、ここにも確認を足す。

## クラウドから確かめられること

Pi のアプリは Tailscale Funnel で https://bg.tail5c266.ts.net/bg/ に公開している（ルートの `/` は 404）。
クラウドの Claude もここには届くので、**外から見えることはクラウドで先に確かめ、`Pi:` の行に「クラウドから」と書いてよい。**

```bash
uv run python tools/check_pi.py          # --all で samples/ の全部
```

`/version`（版とコミット、main からコードが変わっていないか）、静的ファイルが手元と同じか、
`samples/` の公開写真 5 枚を `/analyze-photo`（0-ply）に送り、Pi の読み取りが手元と同じか・正解と何点合うかを出す。
画面は Playwright の Chromium で `/bg/` を開けば見られる。
クラウドの環境によっては、プロキシが ts.net を通さず `Tunnel connection failed: 403` になる（2026-10-14、引き継ぎ先のアカウントで確認）。
そのときでも、Claude の WebFetch ツールでは GET（`/bg/version` など）が読めることがある（2026-10-14、同じアカウントで確認）。
POST（`/analyze-photo`）は送れないので、読み取りの確認は Pi の Claude Code に任せる。

クラウドからは**やらない・できない**こと（Pi の Claude Code かユーザーに残す）:

- `git pull` と `docker compose up -d --build`（Pi の更新そのもの）、コンテナのログ、`collected/` の中身
- `/samples` に送ること（Pi に写真が残る）。送ってよいのはリポジトリで公開している `samples/` の写真だけ
- スマホ実機での操作（カメラ、共有、読み上げ、ホーム画面のアプリ）

## 項目の足し方

マージ後に Pi で確かめる必要がある変更は、**その PR の中でここに項目を足す**。

- 足す前に main を pull し、「次の番号」を使って、その番号を 1 つ進める。
- マージの前に main を取り込んだとき、同じ番号が先に main に入っていたら、自分の方を次の番号に付け直す
  （TODO.md と同じ。コミットのメッセージに「PI-00N に付け直す」と書く）。

```markdown
## PI-00N. 何を確かめるか

- **担当:** ai1（Pi の Claude Code。スマホでの確認は ai1）
- **足した日・PR:** 2026-10-13、PR #42（TODO-018）
- **確かめ方:** 実行するコマンドや手順
- **期待:** どうなれば OK か
- [ ] Pi: （結果をここに書く）
- [ ] スマホ: 見てもらうこと（ai1）　← スマホでの確認がなければこの行は要らない
```

## PI-033. 写真の上に出す文字は数字だけ（analyzer 0.37.0）

- **担当:** ai1（Pi の Claude Code。スマホでの確認は ai1）
- **足した日・PR:** 2026-10-15（ユーザーの依頼: 「キューブは見つかりません」など、数字以外の文字列は不要）
- **確かめ方:** `curl -s http://127.0.0.1:8000/version` が analyzer 0.37.0 以降。Pi の上のヘッドレスのブラウザで、写真を読み込んで四隅探しを、続けて読み取りを見る（`samples/screen2.jpg` など、ダイスとキューブのあるもの）
- **期待:** 四隅探しと読み取りのどの段階でも、写真の上に文字の帯（左下の説明）や「キューブ」の文字が出ない。出る文字はポイントごとの数とダイスの目だけ。
  線・円・四角は今までどおり段階ごとに 1 秒ずつ出て、最後のあとに次へ進む
- [ ] Pi: （結果をここに書く）
- [ ] スマホ: 文字がなくても段階の進みが分かるか（ai1）

## PI-032. キューブ（2・4・8・16）とダイスが写った写真をネットから探して samples/ に足す

- **担当:** ai1（Pi の Claude Code）
- **足した日・PR:** 2026-10-15（TODO-025。ユーザーの依頼: キューブやダイスが写っているサンプルを足して。できればキューブが 2・4・8・16 のもの）
- **なぜ Pi か:** クラウドの環境からは Wikimedia Commons（commons.wikimedia.org・upload.wikimedia.org）に届かない（2026-10-15、プロキシが 403）。
  Pi からは届くので、Pi の Claude Code が探して取り込む。これは確かめる項目ではなく作業の依頼
- **探すもの（上ほど優先）:**
  1. キューブが**片側**（手前か奥、枠の上や盤の横を含む）にあり、数字が **2・4・8・16** のどれかと目で読める写真。値ごとに 1 枚以上、できれば手前と奥の両方
  2. ダイスが盤上にあり、目が読める写真（キューブが 32・64 で片側にあるものも可）
  3. 盤の全体が写っていて、駒が数えられること（斜めでもよいが、四隅が写っていること）
- **探し方と出典の決まり:**
  - まず Wikimedia Commons（`Category:Doubling cubes`、`Category:Backgammon` とその下、検索語 `backgammon cube`・`doubling cube`・`tavla`・`nardy` など）。
    ライセンスが CC0 / CC BY / CC BY-SA のものだけ。Commons の縮小版（長辺 1920px、元が小さければそのまま）を使い、
    `samples/commons-<特徴>.jpg` として置き、[samples/CREDITS.md](../samples/CREDITS.md) の表に出典・作者・ライセンスを足す
  - 人の顔や個人情報が写っていたら使わないか、隠してから入れる（CLAUDE.md の決まり）
  - 著作権のある画像（USBGF などの盤面図、記事や大会の写真）は画像を入れず、`samples/external/` に URL と正解だけを置く（今の bray-* と同じやり方）
- **正解の書き方:** 今の `*.truth.json` と同じ形で目で読む。キューブは `"cube": {"at": "white" | "black" | "centre" | "field", "value": 4}` のように
  **`value` を足す**（数字を読む機能はまだないが、作るときの答えにする）。今の `recognizer/evaluate.py` はキューブを辞書ごと比べるので、
  `at` だけを比べるように直してから測る（recognizer の版はそのディレクトリのコードを変える決まりどおり 1 つ上げ、`trace_cpu.py --update` が要るか確かめる）
- **そのあと:** `recognizer/evaluate.py` で測り、`recognizer/README.md` の表に足し、`check_accuracy.py --update` で基準を書き直す。
  TODO.md の TODO-025 に、値ごとに何枚見つかったか（見つからなかった値も）を書く
- **マージ:** すべて Commons の CC0 / CC BY / CC BY-SA で人が写っていない写真なら、CLAUDE.md の「共同開発」どおりにマージしてよい。
  それ以外（顔を隠した、出典がはっきりしない、など）があれば TODO-030 と同じく自動マージせず、ai1 が見てからマージする
- [ ] Pi: （探した結果と足した枚数をここに書く）

## PI-031. 四隅探しと四隅の合わせ直しも段階ごとに 1 秒ずつ見せる（analyzer 0.36.0、recognizer 0.17.0）

- **担当:** ai1（Pi の Claude Code。スマホでの確認は ai1）
- **足した日・PR:** 2026-10-15（ユーザーの依頼: 四隅の認識の過程もすべて 1 秒間隔でキューイングして見せる。各段階の秒数はあとで変えられるように）
- **確かめ方:** `curl -s http://127.0.0.1:8000/version` が analyzer 0.36.0・recognizer 0.17.0 以降。
  `curl -sN -F image=@samples/photo3.jpg -F stream=true <URL>/find-corners` で行が届くのを見る。`trace_cpu.py check` と `check_accuracy.py`・`check_corners.py --app` が今までどおり（PI-030 と同じ値）。
  スマホで写真を読み込み、そのまま読み取る
- **期待:** `/find-corners` が `edges` → `uprights` → `candidates` → `corners` → `done` の順に返し、`done` の四隅は `stream` なしと同じ。
  スマホでは、写真を読み込むと走査線のあと「横の縁の候補」「縦の縁の候補」「盤らしい四角形の候補を比べています」「四隅が決まりました」が 1 秒ずつ出てから四隅の点が置かれる（タップで飛ばせる）。
  読み取りでは「四隅を枠の線に合わせました（1・2 回目）」「三角形の並びで四隅を合わせ直しました（1・2 回目）」のあと、PI-029 の段階が続く
  （analyzer 0.37.0 から、これらの段階の説明の文字は出ず、線と四角だけが順に出る。PI-033）
- [ ] Pi: （結果をここに書く）
- [ ] スマホ: 四隅探しの見え方と、写真を読み込んでから四隅を動かせるまでの待ち時間（ai1）

## PI-030. 四隅の初期値を新しい作り方で出す（recognizer 0.16.0）

- **担当:** ai1（Pi の Claude Code。スマホでの確認は ai1）
- **足した日・PR:** 2026-10-15（TODO-028）
- **確かめ方:** `curl -s http://127.0.0.1:8000/version` が recognizer 0.16.0 以降。Pi の上で `uv run python recognizer/trace_cpu.py check`（四隅も比べる）と
  `uv run python recognizer/check_corners.py --app` を走らせる。スマホで写真を読み込み、四隅の初期値と、出るまでの時間を見る
- **期待:** `trace_cpu.py check` が「same as the reference」。`check_corners.py --app` が「within 3.6%: 16, further: 8, not found: 0」。
  1 枚の時間（右の列）はこのクラウド環境で 1.0〜1.8 秒なので、Pi では数倍かかりうる。5 秒を大きく超えるならユーザーに報告する
- [x] Pi: 2026-10-15、3421c7e。`/version` は analyzer 0.35.0・recognizer 0.16.0。`trace_cpu.py check` は「same as the reference: every step of every sample」（終了コード 0）。
  `check_corners.py --app` は「within 3.6%: 16, further: 8, not found: 0」。1 枚の時間は Pi でも 0.93〜1.77 秒で、5 秒より十分短い。OK
- [ ] スマホ: ai1 の盤の写真で、四隅の初期値がどれくらい合っているか、出るまで待たされないか（ai1）

## PI-029. 読み取りの途中経過を段階ごとに 1 秒ずつ見せる（analyzer 0.35.0、recognizer 0.15.0）

- **担当:** ai1（Pi の Claude Code。スマホでの確認は ai1）
- **足した日・PR:** 2026-10-15（ユーザーの依頼: 認識はリアルタイムで行い、途中経過は 1 秒ずつキューイングして順に見せ、全部見せ終えたら認識完了）
- **確かめ方:** `curl -s http://127.0.0.1:8000/version` が analyzer 0.35.0・recognizer 0.15.0 以降。
  Pi の上とクラウドから（公開 URL 経由）、`samples/photo3.jpg` を `stream=true` で送り、行が届くたびに時刻を付けて見る:
  `curl -sN -F image=@samples/photo3.jpg -F corners=<photo3.truth.json の四隅> -F home=right -F bottom_colour=1 -F plies=1 -F stream=true <URL>/analyze-photo | while IFS= read -r l; do echo "$(date +%T.%N | cut -c1-12) ${l:0:60}"; done`。
  スマホで写真を読み取る
- **期待:** `board` から `cube` までの 6 行が、認識の進みに合わせて少しずつ届き（Funnel や service worker が最後にまとめていない）、最後に `done`。
  スマホでは、段階ごとに 1 秒ずつ「枠と列を合わせました」「三角形の先」「駒の候補」「数えました（ポイントの外側に数）」「ダイス」「キューブ」が順に出て、
  最後の段階のあとに盤面の画面に進む（タップで飛ばせる）。左下のラベルの先頭が切れていない（TODO-047）
  （analyzer 0.37.0 から、写真の上の段階の説明の文字は出ない。PI-033）
- [x] Pi: 2026-10-15、3421c7e。Pi の上（127.0.0.1:8000）と公開 URL 経由の両方で、`board` → `tips`（+0.0 秒）→ `checkers`（+0.8〜1.0 秒）→ `counts` → `dice`（+1.1〜1.3 秒）→ `cube`（+2.0 秒）→ `done` が
  認識の進みに合わせて届いた（最初の行まで 3.2〜3.6 秒）。Funnel でまとめられていない。なお `corners` は JSON の配列ではなく `749,234,...` のカンマ区切りで渡す（配列だと 422）。OK
- [ ] スマホ: 途中経過の見え方と待ち時間（ai1）


## 完了済み

決着した項目は `archives/pi/` にある（1 項目 1 ファイル）。一覧は [archives/pi/index.md](../archives/pi/index.md)（新しい順）。
