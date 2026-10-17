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
uv run -q --no-project --with playwright python tools/live_view.py   # スマホの大きさの Chromium で開いておき、サービスの版が変わるたびに再読み込み（開いている間、pi_ui_check・ui_snapshot に BG_CDP=http://127.0.0.1:9222 を付けると操作がこの窓のブラウザに見える）
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
- 写真はサーバーで処理するだけで、保存も外へ送ることもしない。例外は次の 2 つだけ
  - **PWA の設定で「Pi に残す」をオンにしたとき**: 解析するたびに写真と直した盤面を Pi の `collected/` に保存する（`POST /samples`、
    `BG_SAMPLES_DIR` を設定したサーバーだけ。2026-10-14 ユーザーが決めた）。`collected/` はリポジトリに自動では入れない
  - **四隅の画面で「Claude に選ばせる」を押したとき**: その写真を `claude -p` に渡す（Anthropic に送られる。`POST /claude-corners`、
    `BG_CLAUDE` を設定したサーバーだけ。2026-10-17 ユーザーが決めた。TODO-082）
- `samples/` の写真と正解の `*.truth.json` はリポジトリに入れて公開している
  （クラウドでも精度を確認できるように）。**人の顔や第三者の投稿は隠してから入れる。**
  screen2 はゲーム盤の画像以外を塗りつぶしてある。写真の大きさと盤の画素は
  変えていないので、`*.truth.json` の四隅の座標はそのまま使える。元の写真は入れない。
  photo1（人の顔が写っていた斜め撮影の写真）は 2026-10-13 にファイルも Git の履歴も削除した。入れ直さない

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
- **PR は小さく、ブランチ名に作業内容を入れる**（例: `claude/recognizer-oblique`）
- **マージ後に確かめる必要がある変更は、その PR の中で TODO.md のその項目に `- [ ] ローカル:` の行を足す**
  arm64（Pi）で `uv sync --frozen` が通るかは確かめない（2026-10-17 ユーザーが決めた。GitHub Actions も arm64 では流さない）
- **マージの直前に最新の main を取り込み、GitHub Actions の `test` が通ってからマージする（`accuracy` が走った PR はそれも。
  文書だけの PR では `test` は走らないので要らない）。** 落ちていたらマージしない。
  テスト全体は手元で流さない（CI と重なる。`.claude/hooks/no-local-pytest.py` が止める）。
  相手の変更とぶつかったら、勝手に直さずユーザーに報告する
