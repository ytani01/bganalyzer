# TODO-056. Docker をやめ、Pi の常駐を uv と systemd にする

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort medium | implementer（Sonnet 5.5 / medium）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |
| 実施 | Opus 5.5 / effort 記載なし | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | 記載なし | 60 | 19,802 | 108,879 | 2,334,455 | 71% |
| reviewer | Opus 5.5 | high | 20 | 3,399 | 64,056 | 430,059 | 14% |
| verifier | Haiku 5.5 | medium | 30 | 99 | 43,894 | 461,968 | 15% |
| 合計 |  |  | 110 | 23,300 | 216,829 | 3,226,482 | 計 3,466,721 |

- 実装は implementer に回さず main が行った。調べ終えた時点で変更の大半が文書の置き換えで、依頼を書く方が重かったため
- reviewer と verifier は定義どおりのモデルと effort を、Agent ツールで同じ値に明示して呼んだ
- 集計は `--since '2026-10-15 19:43:00'`（立てたコミットが TODO-055 の直しと一緒で、始点が見つからないため）から e467f06 まで。
  マージ後の Pi での切り替え（PI-040）と決着の分は入っていない

## きっかけ

TODO-055 で Pi でも `uv sync` が通るようになり、Docker は要らなくなった。Docker は残さず消す（2026-10-15 ユーザーが決めた）。

## やったこと

- `bganalyzer.service`（systemd のユーザー unit）をリポジトリのトップに置いた。`@DIR@` を `sed` でリポジトリのフォルダに置き換えて
  `~/.config/systemd/user/` に入れる。`.venv/bin/uvicorn` を直接起動し（ワーカー 1 つ）、`Restart=always`、`BG_SAMPLES_DIR=@DIR@/collected`。
  再起動のあとログインしなくても動くよう、`loginctl enable-linger` を手順に入れた
- Dockerfile・.dockerignore・compose.yaml・`.github/workflows/docker.yml` を消した。docker の CI の「起動して解析・写真認識・`/version`」は、
  `test` の CI（x86_64 と arm64）に uvicorn を起動して試す手順として移した
- README.md・CLAUDE.md・analyzer/README.md・docs/raspi.md・docs/HANDOVER.md・docs/PI_CHECKS.md の Docker の手順を uv と `systemctl --user` に直した。
  `tools/pi_ui_check.py` の `collect` は `docker compose exec` をやめ、`.venv/bin/python` で `evaluate.py` を走らせ、ファイルを直接消す。
  `tools/check_pi.py` の比べる対象は Dockerfile・compose.yaml の代わりに `bganalyzer.service`。
  `recognizer/collected.py`・`tune.py` の使い方の例と、いくつかのコメントのコンテナのパスを直した（アプリの挙動は変わらないので版は上げていない）
- gnubg-wheel.yml のビルド用コンテナは、Pi と同じ bookworm の glibc でビルドするために残した（アプリは Docker で動かさない）
- Pi での切り替えの手順を PI-040 に書き、マージ後にこの Pi で切り替えた（コンテナとイメージを消し、`collected/` の持ち主を root から戻した）
- 決着のときに、docs/raspi.md のログの見方を `journalctl _SYSTEMD_USER_UNIT=bganalyzer.service -f` に直した。
  書いていた `journalctl --user -u bganalyzer -f` は、この Pi では「No journal files were found」で何も出なかった

## 確かめたこと

- `uv run pytest analyzer` 79 件通過（Pi）。PR #183 の `test`（x86_64・arm64、足した起動の手順を含む）・`accuracy`・`cpu-match` が通った
- verifier: `test.yml` の起動の手順を 8001 番でそのまま実行して通った。unit は `systemd-analyze --user verify` で警告なし。
  `pi_ui_check.py collect` は `collected/` が root 所有のため PermissionError で落ちた（切り替えで持ち主を戻すまでは想定どおり）
- PI-040（Pi の本番）: 切り替えたあと `/version` が 05e210c、`check_pi.py` OK、`pi_ui_check.py collect` OK（24/24）。
  再起動のあと、ログインより前に立ち上がり、`/version` が返った

## 分担の振り返り

- **reviewer** は要修正 2 件を見つけた: uv を入れた直後の同じシェルでは `uv` が見つからない（Docker の手順にあった「ログインし直す」が抜けていた）、
  `check_pi.py` の比べる対象に `bganalyzer.service` が無く、unit を変えても Pi の入れ直しに気づけない。
  ほかに PI_CHECKS の更新手順が PI-040 の前には落ちること、英語の `container` のコメントの残り、ユーザー unit で効かない `After=network-online.target`。どれも直した
- **verifier** は CI の手順と unit が動くことを実測し、`collected/` が root 所有のままだと保存が落ちることを再現した（PI-040 の chown の裏付け）。
  ログの見方の誤りは誰も見つけられず、決着のときに利用者の質問で分かった。verifier に実際の Pi の journal を読ませる確認を入れていなかった
- **見込みとの食い違い:** implementer を使わなかった。調べる段階で変更箇所がほぼ決まり、文書の置き換えが中心だったため
- **次に同じ規模（運用の手順の入れ替え）をやるなら:** 実装は main で足りる。reviewer → verifier の順は保ち、verifier には
  文書に書いた運用のコマンド（ログ、更新、止める）を、本番に触らない範囲でひととおり打たせる。今回のログの誤りはそれで捕まえられた
