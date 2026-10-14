# Raspberry Pi で確かめること

**残っている項目: PI-020、PI-021、PI-022。** これまでに 19 件を決着させた。
新しく足すときは「完了済み」の上に節を作る（新しい番号ほど上）。**次の番号は `PI-023`。**
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

## PI-022. 三角形の辺で駒の有無を確かめる読み方が Pi で動く（recognizer 0.11.0）

- **担当:** ai1（Pi の Claude Code）
- **足した日・PR:** 2026-10-14、TODO-027
- **確かめ方:** コンテナの中で `python recognizer/evaluate.py samples/commons-dark-homeleft.truth.json samples/commons-set-cube-dice.truth.json`
  と `python recognizer/evaluate.py /data/samples/user-*.truth.json` を動かす。`/analyze-photo` に photo3 を送って時間を見る。
- **期待:** `/version` の recognizer が 0.11.0。dark-homeleft 20/24、set-cube-dice 15/24（マージ前に Pi で測った値）。
  `collected/` の組は直す前（23・19・15・18・22）から合計で下がらない（マージ前は 24・19・14・18・22）。1 枚の読み取りが PI-002 の時間（6 秒前後）から大きく延びていない。
- [ ] Pi:

---

## PI-021. 四隅の推定（recognizer 0.10.0）が Pi でも x86_64 と同じくらい当たる

- **担当:** ai1（Pi の Claude Code）
- **足した日・PR:** 2026-10-14（TODO-028）
- **確かめ方:** Pi の `bganalyzer` フォルダで（コンテナには `samples/` が入っていないので写してから測る）
  `docker compose cp samples app:/tmp/samples && docker compose exec -T app sh -c 'python recognizer/check_corners.py /tmp/samples/*.truth.json'`。
  USBGF の盤面図（`samples/external/`、画像は usbgf.org から取る。クラウドからは届かず 0.10.0 では測れていない）も、
  `docker compose exec -T app sh -c 'python recognizer/evaluate.py /tmp/samples/external/*.truth.json > /dev/null; python recognizer/check_corners.py /tmp/samples/external/*.truth.json'` で測る
  （evaluate.py が画像を取ってくる）。終わったら `docker compose exec -T app rm -rf /tmp/samples`
- **期待:** 全 23 枚で x86_64 の値（3.6% 以内 14 枚・それより外 6 枚・見つからない 3 枚、recognizer/README.md の「四隅の推定」）に近い。
  1 枚 2 秒以内。見つからない写真が x86_64 より多ければ、その名前を書いて TODO-028 に足す
- [ ] Pi: （結果をここに書く）

---

## PI-020. 読み取り中の補助線の演出（analyzer 0.27.0、recognizer 0.9.0）

- **担当:** ai1（Pi の Claude Code。スマホでの確認は ai1）
- **足した日・PR:** 2026-10-14、TODO-039
- **確かめ方:** `docker compose up -d --build` のあと `curl -s localhost:8000/version` で版を見る。
  `tools/pi_ui_check.py` などで写真を読み取り、`/analyze-photo` の `geometry` に `tips` と `checkers` が入っていること、
  画面が盤面の画面に進むことを確かめる。スマホでは「盤面を読み取る」を押して、写真に枠・三角形・走査線が重なり、
  結果が返ったら緑の枠・三角形の先・駒の円が出てから盤面の画面に進むかを見る。
- **期待:** 版が analyzer 0.27.0・recognizer 0.10.0（あとから入った TODO-028 で上がった。0.9.0 でもこの演出は同じ）。演出がカクつかず、タップで飛ばせる。読み取りにかかる時間は前と変わらない（演出の分の約 1.5 秒を除く）
- [ ] Pi: （結果をここに書く）
- [ ] スマホ: 演出が出るか、カクつかないか、タップで飛ばせるか（ai1）

---

## 完了済み

決着した項目は `archives/pi/` にある（1 項目 1 ファイル）。一覧は [archives/pi/index.md](../archives/pi/index.md)（新しい順）。
