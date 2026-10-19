# CLAUDE.md（bganalyzer）

バックギャモン盤の写真から局面を読み取り、GNU Backgammon で解析する。
全体の構成は [README.md](README.md)、各部の詳細は
[recognizer/README.md](recognizer/README.md) と [analyzer/README.md](analyzer/README.md)。

## コマンド

```bash
uv sync                                                          # 依存を .venv に入れる（uv.lock どおり）
uv run pytest analyzer/test_<名前>.py                            # テストを 1 ファイルだけ（全体は GitHub Actions の test が流す。手元で全体を流すと hook が止める）
uv run uvicorn app:app --app-dir analyzer --host 0.0.0.0 --port 8000   # API と PWA（/）の起動
git pull && uv sync --frozen && systemctl --user restart bganalyzer   # Raspberry Pi の常駐を更新（docs/raspi.md）
uv run python recognizer/board.py <写真> --corners ... --home left|right   # 認識だけ試す
uv run python recognizer/check_accuracy.py                       # 認識の精度が基準より下がっていないか（CI の accuracy）
uv run python tools/check_pi.py                                  # Pi の公開サーバーを外から確かめる
uv run -q --no-project --with playwright python tools/pi_ui_check.py   # ローカルホストで、スマホの代わりに PWA を操作して確かめる
uv run -q --no-project --with playwright python tools/ui_snapshot.py record a.json   # PWA を操作して見える画面を記録（compare a.json b.json で 2 つの版を比べる）
uv run -q --no-project --with playwright python tools/live_view.py   # スマホの大きさの Chromium で開いておき、サービスの版が変わるたびに再読み込み。窓でダウンロードしたファイルは ~/Downloads に保存する（開いている間、pi_ui_check・ui_snapshot に BG_CDP=http://127.0.0.1:9222 を付けると操作がこの窓のブラウザに見える）
```

## 変えないもの

- **Python の依存は uv で管理する。** 追加・削除は `uv add` / `uv remove`
  （テスト用は `--dev`）で行い、`pyproject.toml` と `uv.lock` を一緒にコミットする。
  Pi も `uv sync --frozen` で同じ `uv.lock` から入れる（Docker は使わない。TODO-056）
- **API は `--reload` や複数ワーカーで動かさない。** gnubg はメインスレッド以外で
  評価するとクラッシュするので、解析は専用の子プロセスで行っている
  （`analyzer/engine.py`）
- **色の呼び方: white = 写真の手前のプレイヤー、black = 奥のプレイヤー。**
  `points[i]` は手前側から見たポイント i+1、正が white、負が black。
  認識と解析で揃えている
- 写真はサーバーで処理するだけで、保存も外へ送ることもしない。例外は次の 3 つだけ
  - **盤面の画面の「サーバーに［保存する］」のとき（既定。2026-10-17 ユーザーが既定を保存するに変えた。TODO-112）**: 解析するたびに写真と直した盤面を Pi の `collected/` に保存する（`POST /samples`、
    `BG_SAMPLES_DIR` を設定したサーバーだけ。2026-10-14 ユーザーが決めた）。`collected/` そのものはリポジトリに入れない（読み違いのある組だけ、下のとおり `samples/` に自動で入る）
  - **四隅の画面で「Claude に選ばせる」を押したとき**: その写真を `claude -p` に渡す（Anthropic に送られる。`POST /claude-corners`、
    `BG_CLAUDE` を設定したサーバーだけ。2026-10-17 ユーザーが決めた。TODO-082）
  - **開発機が読み違いの組を `samples/` に取り込むとき**: 盤の外を塗った写真を `claude -p` に渡して名前を付けさせる（`BG_IMPORT` と `BG_CLAUDE` を設定したサーバーだけ。
    どのみち公開する写真なので、公開より前に送るだけ。2026-10-19 ユーザーが決めた。TODO-142）
- 写真ではないが、**結果の「読み上げ」の文は Google に送る**: サーバーが 1 文ずつ Google 翻訳の読み上げ（`translate_tts`、公式でない API）に送り、
  返ってきた音声を鳴らす（`GET /speech`。どの端末でも同じ声にするため。2026-10-17 ユーザーが決めた。TODO-111）。止まったときはブラウザの音声合成で読む。
  ほかの 3 つと違い、設定なしでいつも動く（公開しているので誰でも Pi を通して送れるが、送れるのは 200 文字までの文だけで、悪用されても Google に断られてブラウザの声に替わるだけ。2026-10-17 ユーザーが決めた）
- `samples/` の写真と正解の `*.truth.json` はリポジトリに入れて公開している
  （クラウドでも精度を確認できるように）。**手で入れるときは、人の顔や第三者の投稿を隠してから入れる。**
  screen-app-green-far はゲーム盤の画像以外を塗りつぶしてある。写真の大きさと盤の画素は
  変えていないので、`*.truth.json` の四隅の座標はそのまま使える。元の写真は入れない。
  photo1（人の顔が写っていた斜め撮影の写真）は 2026-10-13 にファイルも Git の履歴も削除した。入れ直さない
- `collected/` の読み違いのある組は、開発機（`BG_IMPORT` を設定したサーバー。誰でも送れる Pi では動かさない）で
  `recognizer/import_collected.py` が盤の外を黒く塗って `samples/collected-*` に入れ、PR をマージまで自動で進める（TODO-114）。
  **盤の上に写った手や物、直し忘れた正解はそのまま公開される**（2026-10-17 ユーザーが決めた）。見つけたら、写っていけないものを手で黒く塗りつぶすか、その組を消す PR を出す

## バージョン

analyzer と recognizer は別々にバージョンを持つ（`analyzer/app.py` と `recognizer/board.py` の `__version__`）。
API の `/version` と PWA のヘッダーに、両方とコミット ID が出る。
**そのディレクトリのコードを変える PR で、その方を上げる**（直しは 0.1.0 → 0.1.1、機能の追加や変更は 0.1.0 → 0.2.0）。
analyzer を上げるときは `analyzer/static/app.js` の `APP_VERSION` も同じにする（端末に古い app.js が残っているとヘッダーに出る）。
ドキュメントやテストだけの変更では上げない。recognizer の測る道具（`evaluate.py`・`check_accuracy.py`・`check_corners.py`・`collected.py` の比べ方など）だけの変更でも上げない（アプリの読み取りの結果は変わらないため。2026-10-15 ユーザーが決めた）。`pyproject.toml` の version は使わない。

## 精度の確認

認識を変えたら `recognizer/evaluate.py` で `samples/*.truth.json` と比べ、
`recognizer/README.md` の「精度」の表を更新する。
GitHub Actions の `accuracy` は、サンプルごとの結果が `recognizer/accuracy_baseline.json` より悪くなると落ちる。
良くなったとき・サンプルを足した／消したときは `uv run python recognizer/check_accuracy.py --update` で基準を書き直して同じ PR に入れる。

CPU による読みの違いは気にしない（TODO-074）。今の読み取りは整数と `recognizer/exact.py` で計算していて、どの機械でも同じに読むので、
基準はどの機械（Pi でも）で更新してよい。これからの変更で float の処理を使ってもよい。
そのせいで Pi と GitHub Actions で結果が分かれたら、GitHub Actions の結果に合わせて基準を書き直す。

## マージ後に確かめること

マージ後に動いているアプリでしか確かめられないことは、Raspberry Pi ではなく**ローカルホスト（開発機）で確かめ**、
**TODO.md のその項目に書く**（`- [ ] ローカル:` / `- [ ] スマホ:` の行。項目はその確認まで済んでから決着させる）。
開発機にも Pi と同じ `bganalyzer.service` を入れてある。
2026-10-17 に docs/PI_CHECKS.md の決まりをやめた（決着した PI-001〜PI-050 は `archives/pi/` に残す）。
**`git pull` のあと、ローカルホストでアプリを更新して TODO.md の `- [ ] ローカル:` の行を確かめ、結果を書き込む**
（更新と確かめ方は [docs/raspi.md](docs/raspi.md) の「ふだんの運用」「更新したあとに確かめる」）。
期待と違えばユーザーに報告する。
公開している https://bg.tail5c266.ts.net/bg/ にはクラウドからも届くので、版・画面・公開サンプルの読み取りは
**クラウドの Claude が `uv run python tools/check_pi.py` で先に確かめてよい**（やり方とやらないことは docs/raspi.md の「クラウドから確かめられること」）。

## アプリの画面を見せるとき

アプリの画面をユーザーに見せる場面では、スクリーンショットを撮って添付する代わりに、`tools/live_view.py` のブラウザを操作して見せる
（2026-10-17 ユーザーが決めた。TODO-108）。開いていなければ live_view を起動し、Playwright から `connect_over_cdp("http://127.0.0.1:9222")` で
そのブラウザにつないで操作する（`tools/pi_ui_check.py`・`tools/ui_snapshot.py` は `BG_CDP=http://127.0.0.1:9222` を付ける）。
担当（teammate）に画面を操作させるときも、依頼に `BG_CDP` を付けるよう書く。

## タスク管理

`TODO.md` で管理する（書式は `~/.claude/CLAUDE.md` と `todo-workflow` skill）。
項目に担当は書かない（2026-10-15 ユーザーが決めた）。

## 共同開発

このリポジトリは、別のアカウントの Claude プロジェクトからも同時に開発する
（手順は [docs/HANDOVER.md](docs/HANDOVER.md)）。
文書の「ユーザー」はこのリポジトリの持ち主のこと。`archives/` や古いコミットでは「ai1」と書いてある。

- **方針・進み具合・決まったことはリポジトリに書く。** Claude のプロジェクトのメモは相手から見えない。
  ルールはこの CLAUDE.md、作業は `TODO.md`、進み具合と未決事項は `docs/HANDOVER.md`
- **作業の前に main を pull する。**
- **同じマシンで並べて作業するときは、セッションごとに worktree を分ける**（2026-10-19 ユーザーが決めた）。
  `claude -w <名前>` で起動し（`.claude/worktrees/<名前>/` に別のブランチの作業ツリーができる）、`claude agents` で見渡す。
  トップの作業ツリー（`~/work/bganalyzer`）は main のままにしておく。ローカルホストの `bganalyzer.service` と post-merge の再起動はここを見ているので、
  マージ後の更新と `- [ ] ローカル:` の確認は、ここで `git pull` してから行う
- **main（利用者と話すセッション）は利用者との対話に専念する**（2026-10-19 ユーザーが決めた）。
  main が自分でやるのは、調べる（要点を短く読む程度）・利用者に聞く・担当に頼む・担当の報告を読むことだけ。
  TODO の項目を立てる・決着させる、コードや文書の変更、コミット・PR・マージ、マージ後のローカルの確認は、すべて担当（teammate）にさせる。
  teammate は Agent ツールに `name` を付けて起動し、`isolation` は付けない（付けると teammate にならない）。bganalyzer だけで有効にしている（`.claude/settings.local.json`。リポジトリには入らない）。
  teammate は main と同じトップの作業ツリーで起動するので、**作業の最初に自分で `git worktree add .claude/worktrees/<名前> -b claude/<作業内容> origin/main` を作り、その中で編集・コミット・PR まで行う**。トップは main のままにする。
  同じファイルを複数の担当に同時に編集させない。
  tmux で開いた teammate には SendMessage が無いことがあるので、main に確認を頼むときは、作業を止めて返事（終わったときの通知）で伝える。
  確認・レビューを別の担当に分ける決まり（`~/.claude/CLAUDE.md`）はそのまま。ローカルの確認は、担当がトップの作業ツリー（main のまま）で `git pull` だけ行ってから確かめる（TODO-154）
- **PR は小さく、ブランチ名に作業内容を入れる**（例: `claude/recognizer-oblique`）
- **マージ後に確かめる必要がある変更は、その PR の中で TODO.md のその項目に `- [ ] ローカル:` の行を足す**
  arm64（Pi）で `uv sync --frozen` が通るかは確かめない（2026-10-17 ユーザーが決めた。GitHub Actions も arm64 では流さない）
- **マージの直前に最新の main を取り込み、GitHub Actions の `test` が通ってからマージする（`accuracy` が走った PR はそれも。
  文書だけの PR では `test` は走らないので要らない）。** 落ちていたらマージしない。
  テスト全体は手元で流さない（CI と重なる。`.claude/hooks/no-local-pytest.py` が止める）。
  相手の変更とぶつかったら、勝手に直さずユーザーに報告する
