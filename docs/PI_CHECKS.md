# Raspberry Pi で確かめること

**残っている項目: PI-013、PI-014、PI-015、PI-017。** これまでに 13 件を決着させた。
新しく足すときは「完了済み」の上に節を作る（新しい番号ほど上）。**次の番号は `PI-018`。**
各項目の最初に **担当** を書く。決まりは [TODO.md](../TODO.md) と同じ（[CLAUDE.md](../CLAUDE.md) の「Raspberry Pi で確かめること」）。

マージしたあと、自宅の Raspberry Pi（公開している本番）でしか確かめられないことの一覧です。
クラウドの Claude は Pi に入れないので、**Pi の上で動く Claude Code がここを読んで確かめ、結果を書き込みます。**
外から見えること（版、画面、公開サンプルの読み取り）は、下の「クラウドから確かめられること」でクラウドからも確かめられます。

## Pi の上の Claude Code がやること

1. `bganalyzer` フォルダで `git pull` し、`docker compose up -d --build` でアプリを更新する（手順の詳細は [raspi.md](raspi.md) の「ふだんの運用」）。
2. `curl -s http://127.0.0.1:8000/version` が、pull した main の版とコミットになっているか確かめる。
3. 残っている項目の `- [ ] Pi:` を確かめ、`- [x] Pi: 日付、コミット。測った値。OK か` に書き換える。
   スマホの画面など Pi だけでは確かめられないことは `- [ ] スマホ:` の行に残し、ユーザーに頼む。
4. 項目のチェックが全部付いたら、項目を `archives/pi/PI-00N. 題名.md` に移して「**日付 に完了:**」を書き足し、
   [archives/pi/index.md](../archives/pi/index.md) のいちばん上に 1 行足し、上の「残っている項目」と件数を直す。
   ユーザーがスマホで見て OK と言ったときも同じ。
5. 期待と違ったら（遅すぎる・落ちる・値が違う）、ユーザーに報告し、TODO.md に項目を足す。
6. ブランチを切って PR にし、CLAUDE.md の「共同開発」どおりにマージする（main に直接 push しない）。

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

---

## PI-017. 「ダブルされた」のまま写真を読んでも、写真のダイスで最善手が出る（analyzer 0.25.2）

- **担当:** ai1（Pi の Claude Code。スマホでの確認は ai1）
- **足した日・PR:** 2026-10-14、TODO-033
- **確かめ方:** `git pull && docker compose up -d --build`。`curl -s http://127.0.0.1:8000/version` を見る。
  ユーザーにスマホで、キューブを片側に置いて「ダブルされたところ」にしたまま、ダイスの写った写真を読み取ってもらう。
- **期待:** `/version` が analyzer 0.25.2。読み取りが 422 にならず、写真のダイスが入って最善手が出る。キューブの説明が「ダイスがあるので、最善手を出します。」になる。
- [x] Pi: 2026-10-14、701d757。`/version` は analyzer 0.25.2・recognizer 0.7.0。`samples/screen1.png` を `doubled=true`・`cube_owner=white`・ダイスなしで送ると 200 になり、写真のダイス 4-2 で最善手 `24/20 13/11` が出た（ダイスの写ったサンプル 10 枚も 422 なし）。OK
- [ ] スマホ: 上の操作で最善手が出る（ai1）

---

## PI-015. 「Pi に残す」で写真と直した盤面が collected/ に入る（analyzer 0.25.0）

- **担当:** ai1（Pi の Claude Code。スマホでの確認は ai1）
- **足した日・PR:** 2026-10-14、Pi への自動保存（TODO-030）
- **確かめ方:** `git pull && docker compose up -d --build`（compose.yaml が変わったので作り直しになる）。`curl -s http://127.0.0.1:8000/version` の `samples` を見る。
  ユーザーにスマホで「解析の設定」の「Pi に残す」をオンにして 1 枚解析してもらい、`ls -l collected/` と
  `docker compose exec app sh -c 'python recognizer/evaluate.py /data/samples/*.truth.json'` を実行する。
- **期待:** `/version` が analyzer 0.25.0 以上で `"samples": true`。解析したあと `collected/` に `user-*.jpg` と `user-*.truth.json` が 1 組でき、evaluate.py で測れる。
  オフのままなら何も増えない。
- [ ] Pi: 2026-10-14、クラウドから。`/version` は analyzer 0.25.1・`"samples": true`（359d6a5）。`collected/` に入るかは Pi で見る
- [ ] スマホ: 「解析の設定」の下に「精度の改善」のスイッチが出て、オンにして解析できる（ai1）

---

## PI-014. 盤面の画面の「精度改善用に書き出す」（analyzer 0.24.0）

- **担当:** ai1（Pi の Claude Code。スマホでの確認は ai1）
- **足した日・PR:** 2026-10-14、精度改善用の書き出し（TODO-030）
- **確かめ方:** 更新のあと `/version` と `/sample.js` を見る。スマホで写真を読み取り、盤面の画面の「精度改善用に書き出す」を押す。
- **期待:** `/version` が analyzer 0.24.0（かそれ以降）、`/sample.js` が 200。スマホでは共有の画面が開くか（iPhone など）、2 つともダウンロードされ（Android の Chrome）、
  写真と `.truth.json` の 2 つのファイルを保存したり送ったりできる。
- [x] Pi: 2026-10-14、d312151。`/version` は analyzer 0.24.0・recognizer 0.6.2、`/sample.js` は 200。OK
- [ ] スマホ: 書き出した 2 つのファイルを、プロジェクトのチャットに添付できる（ai1）

---

## PI-013. 読み上げが概要だけになる（analyzer 0.23.0）

- **担当:** ai1（Pi の Claude Code。スマホでの確認は ai1）
- **足した日・PR:** 2026-10-14、読み上げを概要だけにする PR
- **確かめ方:** Pi で `curl -s http://127.0.0.1:8000/version`。スマホで写真を解析し、ヘッダーの 🔊 を押す
- **期待:** analyzer が 0.23.0 以上。読み上げは最善手・キューブの判断・形勢（「かなり有利」「ほぼ互角」など）だけで、勝率やピップ数の数字を読まない
- [x] Pi: 2026-10-14、d312151。`/version` は analyzer 0.24.0（0.23.0 以上）。OK
- [ ] スマホ: 🔊 の読み上げが手短な概要になっている（ai1）

---

## 完了済み

決着した項目は `archives/pi/` にある（1 項目 1 ファイル）。一覧は [archives/pi/index.md](../archives/pi/index.md)（新しい順）。
