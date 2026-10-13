# CLAUDE.md（bganalyzer）

バックギャモン盤の写真から局面を読み取り、GNU Backgammon で解析する。
全体の構成は [README.md](README.md)、各部の詳細は
[recognizer/README.md](recognizer/README.md) と [analyzer/README.md](analyzer/README.md)。

## コマンド

```bash
uv sync                                                          # 依存を .venv に入れる（uv.lock どおり）
uv run pytest analyzer                                           # テスト
uv run uvicorn app:app --app-dir analyzer --host 0.0.0.0 --port 8000   # API と PWA（/）の起動
docker build -t bganalyzer . && docker run --rm -p 8000:8000 bganalyzer   # コンテナで起動
docker compose up -d --build                                     # Raspberry Pi で常駐（docs/raspi.md）
uv run python recognizer/board.py <写真> --corners ... --home left|right   # 認識だけ試す
```

## 変えないもの

- **Python の依存は uv で管理する。** 追加・削除は `uv add` / `uv remove`
  （テスト用は `--dev`）で行い、`pyproject.toml` と `uv.lock` を一緒にコミットする。
  Docker も `uv sync --frozen` で同じ `uv.lock` から入れる
- **API は `--reload` や複数ワーカーで動かさない。** gnubg はメインスレッド以外で
  評価するとクラッシュするので、解析は専用の子プロセスで行っている
  （`analyzer/analysis.py`）
- **色の呼び方: white = 写真の手前のプレイヤー、black = 奥のプレイヤー。**
  `points[i]` は手前側から見たポイント i+1、正が white、負が black。
  認識と解析で揃えている
- 写真はサーバーで処理するだけで保存しない
- `samples/` の写真と正解の `*.truth.json` はリポジトリに入れて公開している
  （クラウドでも精度を確認できるように）。**人の顔や第三者の投稿は隠してから入れる。**
  screen2 はゲーム盤の画像以外を塗りつぶしてある。写真の大きさと盤の画素は
  変えていないので、`*.truth.json` の四隅の座標はそのまま使える。元の写真は入れない。
  photo1（人の顔が写っていた斜め撮影の写真）は 2026-10-13 にファイルも Git の履歴も削除した。入れ直さない

## バージョン

analyzer と recognizer は別々にバージョンを持つ（`analyzer/app.py` と `recognizer/board.py` の `__version__`）。
API の `/version` と PWA の画面の下に、両方とコミット ID が出る。
**そのディレクトリのコードを変える PR で、その方を上げる**（直しは 0.1.0 → 0.1.1、機能の追加や変更は 0.1.0 → 0.2.0）。
analyzer を上げるときは `analyzer/static/app.js` の `APP_VERSION` も同じにする（端末に古い app.js が残っていると画面の下に出る）。
ドキュメントやテストだけの変更では上げない。`pyproject.toml` の version は使わない。

## 精度の確認

認識を変えたら `recognizer/evaluate.py` で `samples/*.truth.json` と比べ、
`recognizer/README.md` の「精度」の表を更新する。

## Raspberry Pi で確かめること

マージ後に自宅の Raspberry Pi（本番）でしか確かめられないことは [docs/PI_CHECKS.md](docs/PI_CHECKS.md) で、
**TODO.md と同じ決まり**で管理する（`PI-001` からの通し番号、ファイルの先頭に「残っている項目」と「次の番号」、
各項目に **担当**、状態は `- [ ]` / `- [x]`、決着したら `archives/pi/` に 1 項目 1 ファイルで移す）。
**Raspberry Pi の上で作業する Claude Code は、`git pull` のあとに docs/PI_CHECKS.md を読み、**
**残っている項目を確かめて結果を書き込む**（アプリの更新は `docker compose up -d --build`、詳しくは [docs/raspi.md](docs/raspi.md)）。
期待と違えばユーザーに報告する。

## タスク管理

`TODO.md` で管理する（書式は `~/.claude/CLAUDE.md` と `todo-workflow` skill）。
各項目には **担当** を書く。担当が自分（このプロジェクトのユーザー）でない項目のファイルは触らない。

## 共同開発

このリポジトリは、別のアカウントの Claude プロジェクトからも同時に開発する
（手順は [docs/HANDOVER.md](docs/HANDOVER.md)）。

- **方針・進み具合・決まったことはリポジトリに書く。** Claude のプロジェクトのメモは相手から見えない。
  ルールはこの CLAUDE.md、作業と担当は `TODO.md`、進み具合と未決事項は `docs/HANDOVER.md`
- **作業の前に main を pull する。** 着手する TODO の担当を自分にして、先にコミットしておく
- **PR は小さく、ブランチ名に作業内容を入れる**（例: `claude/recognizer-oblique`）
- **マージ後に Pi で確かめる必要がある変更は、その PR の中で docs/PI_CHECKS.md に項目を足す**
- **マージの直前に最新の main を取り込み、`uv run pytest analyzer` と GitHub Actions の `test` が
  両方通ってからマージする。** どちらかが落ちていたらマージしない。
  相手の担当の部分とぶつかったら、勝手に直さずユーザーに報告する
