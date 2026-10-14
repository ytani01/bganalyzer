# Raspberry Pi で確かめること

**残っている項目: PI-025、PI-027。** これまでに 25 件を決着させた。
新しく足すときは「完了済み」の上に節を作る（新しい番号ほど上）。**次の番号は `PI-028`。**
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

## PI-027. 模様のある駒の面を読む（recognizer 0.13.1）

- **担当:** ai1（Pi の Claude Code）
- **足した日・PR:** 2026-10-15（TODO-044）
- **確かめ方:** `curl -s http://127.0.0.1:8000/version` が recognizer 0.13.1 以降。Pi で `uv run python recognizer/check_accuracy.py` を走らせ（基準は更新しない）、
  サンプルごとのポイントを前の Pi の値と比べる
- **期待:** tv-vegas-open の 6 ポイント（手前の 1 個）を読む。ほかのサンプルは前より下がらない（Pi と x86_64 の違いは TODO-046 で揃える）
- [ ] Pi: （結果をここに書く）

## PI-025. 読み取りの演出で駒・ダイス・キューブを約 0.5 秒ずつ見せる（analyzer 0.33.0、recognizer 0.12.0）

- **担当:** ai1（Pi の Claude Code。スマホでの確認は ai1）
- **足した日・PR:** 2026-10-14（ユーザーの依頼）
- **確かめ方:** `curl -s http://127.0.0.1:8000/version` が analyzer 0.33.0・recognizer 0.12.0 以降。`samples/screen1.png` と `samples/screen2.jpg` を `/analyze-photo` に送り、`geometry` の `dice` と `cube` を見る。スマホで、ダイスとキューブの写った写真を読み取る
- **期待:** screen1 は `dice` の目が 4 と 2、`cube` は null。screen2 は `dice` の目が 5 と 4、`cube.at` が `"black"`（x86_64 と同じ）。スマホでは、駒の円のあと、ダイスに水色の四角と目、キューブに桃色の四角が順に出て、約 2 秒で盤面の画面に進む（タップで飛ばせる）
- [x] Pi: 2026-10-14、db18668。`/version` は analyzer 0.33.0・recognizer 0.12.0。screen1 は `dice` 4・2、`cube` null。screen2 は `dice` 4・5、`cube.at` `"black"`。OK。
  ヘッドレスの Chromium（412×915）で screen2 を読み取ると、応答から 0.95 秒で駒の円、1.45 秒でダイスの水色の四角と目、1.8 秒でキューブの桃色の四角が出て、2.44 秒で盤面の画面に進んだ。OK。
  ただし左下のラベルの先頭が切れる（「ダイス 4・5」が「ゞイス 4・5」、「キューブ（奥）」が「ューブ（奥）」）
- [ ] スマホ: 演出の見え方と長さ（ai1）

## 完了済み

決着した項目は `archives/pi/` にある（1 項目 1 ファイル）。一覧は [archives/pi/index.md](../archives/pi/index.md)（新しい順）。
