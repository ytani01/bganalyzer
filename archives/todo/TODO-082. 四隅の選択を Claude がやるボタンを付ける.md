# TODO-082. 四隅の選択を Claude がやるボタンを付ける

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort high | main（設計）+ implementer（Opus 5.5 / medium）+ reviewer（Opus 5.5 / high）+ verifier（Sonnet 5.5 / medium） |
| 実施 | Opus 5.5 / effort 記載なし（このセッションの設定のまま） | main（試し・設計）+ implementer（Opus 5.5 / medium）+ reviewer（Opus 5.5 / high）+ verifier（Sonnet 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | 記載なし | 92 | 22,000 | 163,191 | 3,553,645 | 43% |
| implementer | Opus 5.5 | medium | 80 | 5,007 | 206,166 | 2,767,760 | 34% |
| reviewer | Opus 5.5 | high | 40 | 4,032 | 76,973 | 1,022,963 | 13% |
| verifier | Sonnet 5.5 | medium | 44 | 318 | 54,356 | 879,651 | 11% |
| 合計 |  |  | 256 | 31,357 | 500,686 | 8,224,019 | 計 8,756,318 |

- implementer は定義のモデルが sonnet。API の子プロセスの扱いが込み入るので、見込みどおり Opus 5.5 に上書きした（effort は定義と同じ medium を Agent ツールで渡した）
- verifier は定義のモデルが haiku。Playwright で操作し、偽のプロセスの消え方まで測るので、見込みどおり Sonnet 5.5 に上書きした
- reviewer は定義のまま（Opus 5.5 / high）
- 担当の effort は、見込みに書いた値を Agent ツールの `effort` で渡した

## きっかけ

ユーザーの依頼（2026-10-17）。自動の四隅の推定が外れる写真（photo5・photo6 など、TODO-078）で、手で直す手間を減らしたい。
四隅の画面に「Claude に選ばせる」ボタンを置き、押すとサーバーが `claude -p` に写真を渡して四隅を答えさせる。

決めたこと（ユーザー）: ボタンは環境変数で有効にしたサーバーだけ。押したときだけ写真が Anthropic に送られる（CLAUDE.md に例外として書く）。
子プロセスは時間切れ・切断・取り消しで殺し、同時に走らせる数を絞る。

## やったこと

- 試し（`archives/agents/TODO-082/try_claude.py`・`try_claude.txt`）: photo5・photo6・collected-2aunci の 3 枚で Sonnet 5.5 と Opus 5.5 を比べた。
  ずれはどちらも長辺の 1〜4%、6〜9 秒。ユーザーが **Sonnet 5.5** に決めた（環境変数 `BG_CLAUDE_MODEL` で変えられる）
  - `--setting-sources ""` で利用者の設定と hook を読まないようにすると、入力が 2.3 万から約 6 千トークンに減った。ただし考えずに答えて大きく外れる回が出たので、
    `--effort high` を付け、角ごとに 1 行説明させてから JSON を書かせる形にした（ずれ 0.7〜3.2%）
- API: `analyzer/claude_corners.py`（新しいモジュール）の `POST /claude-corners`。有効にするのは `BG_CLAUDE`（`claude` のパス）を設定したときだけ。`/version` に `claude` を追加
  - 写真を長辺 1568px に縮め、stream-json の image ブロックで渡す。ツールは使わせない
  - 子プロセスは `start_new_session` で起こし、時間切れ（60 秒、504）と切断のときに `killpg` でグループごと殺す。同時は 1 本で、2 本目は 429。
    返事が読めない、値が有限でない、起動できない場合は 502
- PWA: 四隅の画面に「Claude に選ばせる」ボタン（`/version` の `claude` が true のときだけ）と注意の一文。待つ間の表示に「取り消す」（`AbortController`）。
  置き換えたら `cornersFixed` を戻す。analyzer 0.49.0
- 文書: CLAUDE.md の写真の扱いの例外、README.md・analyzer/README.md、`bganalyzer.service` のコメント、docs/raspi.md（`systemctl --user edit` の drop-in で有効にする）、docs/PI_CHECKS.md の PI-049
- 回数の上限は付けない（公開サーバーだが、同時 1 本だけにする。ユーザーが決めた）

## 確かめたこと

- テスト（`analyzer/test_api.py` の `-k claude` の 3 本）: 本物の `claude` は呼ばず、偽のコマンドを起動するのは 3 回だけ（ユーザーの依頼）。成功と縮尺の戻し、無効のときの 404・`/version`、壊れた返事の 502、時間切れの 504 で子まで消えること、同時 2 本目の 429
- verifier（`archives/agents/TODO-082/verifier-report.md`）: NaN・存在しないパスで 502、Playwright でボタンの出し分け、偽が返した四隅との差 0、取り消しの 0.5 秒後に偽のプロセスが消える、続けて押しても 429 にならない、`cornersFixed` が戻る、画面のスクリーンショット
- GitHub Actions の test が通ってからマージした（PR #247）

## 残ること

- Pi で本物を押して確かめる（PI-049。本物を押すのは 2 回だけ。Funnel 越しの取り消しも見る）

## 分担の振り返り

- **各担当が見つけたこと:** reviewer は、claude 本体が先に終わると残った子を殺さないこと、NaN が 500 になること、CLAUDE.md の文面の矛盾、Git で管理している unit を書き換えさせる手順など 10 件を見つけ、直すべき 2 件は偽のコマンドで再現していた。
  verifier は食い違いを見つけなかった（取り消し後の表示と、自動検出中に押せる点を挙げたが、どちらも意図どおりだった）。implementer は CLAUDE.md を触らない決まりで、写真の扱いの例外を main に残した
- **見込みとの食い違い:** 分担は見込みどおり。main の試しが、`--setting-sources ""` で考えずに答える回が出たため 3 回に割れた
- **次に同じ規模なら:** 同じ組み方でよい。ただし、子プロセスを扱う設計では「本体が先に終わり子が残る」の場合を、設計の段階で design.md に書いておく（reviewer の指摘で直しが 1 巡増えた）。
  試しでは、利用者の設定を外した呼び方を最初から使う（設定の有無で答え方が変わり、測り直しになった）
