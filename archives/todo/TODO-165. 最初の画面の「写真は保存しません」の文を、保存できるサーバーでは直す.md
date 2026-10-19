# TODO-165. 最初の画面の「写真は保存しません」の文を、保存できるサーバーでは直す

|      | main | 担当 |
|------|------|------|
| 見込み | Sonnet 5.5 / effort medium | implementer（Sonnet 5.5）+ reviewer（Opus 5.5 / high）+ verifier（Sonnet 5.5 / medium） |
| 実施 | Opus 5.5 / effort 記載なし | implementer（teammate、Sonnet 5.5 / 記載なし）+ reviewer（teammate、記載なし）+ verifier（teammate、Sonnet 5.5 / 記載なし） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main（teammate の分を含む） | Opus 5.5 + Sonnet 5.5 | 記載なし | 188 | 55,178 | 303,504 | 5,261,436 | 100% |
| 合計 |  |  | 188 | 55,178 | 303,504 | 5,261,436 | 計 5,620,306 |

- teammate の分は main の行に含まれる（`token-usage.py` は teammate を分けて数えない）。モデル別の内訳は Opus 5.5 が 82%、Sonnet 5.5 が 18%
- 範囲は `--since '2026-10-20 02:20:10'`（立てた直後）から作業の最後のコミット（`8483aa2`）まで。そのあとの確認の報告のコミットと、ローカルの確認は含まない

## きっかけ

最初の画面（写真を選ぶ画面）に「写真はサーバーで読み取るだけで、保存しません。」とあった。
TODO-112 で「サーバーに保存する」が既定になったので、保存できるサーバー（`BG_SAMPLES_DIR` を設定したもの）では事実と合わない。
外部の方（バックギャモンの世界チャンピオンや日本バックギャモン協会）に見てもらう前に直すことにした。

決めたこと（2026-10-20 ユーザー）: 保存できるサーバーでは、解析すると写真と盤面を保存し、読み違えた写真は盤の外を黒く塗って公開のサンプルに入れることがある、盤面の画面で保存しないにできる、という趣旨に書き換える。保存できないサーバーでは今の文のまま。盤面の画面の文は変えない。

## やったこと

- `analyzer/static/index.html`: 元の文に `id="photo-note"`、保存できるサーバー用の文 `#photo-note-keep`（`hidden`）を足した
- `analyzer/static/app.js`: `/version` の結果で `serverKeepsSamples` を決めた直後に、2 つの文の `hidden` を切り替える。盤面の画面の `#collect-opt` と同じ変数で、新しい判定は作っていない
- `analyzer/README.md` の `samples` の説明に、最初の画面の文も切り替わることを足した（reviewer の指摘）
- analyzer を 0.90.1 → 0.90.2（`analyzer/app.py` の `__version__`、`analyzer/static/app.js` の `APP_VERSION`）

## 確かめたこと

- `uv run pytest analyzer/test_api.py`: 版の一致は通った。worktree では `.git` がファイルなので commit の比較（`test_version_reports_both_parts_and_commit`）だけ落ちたが、GitHub Actions の `test` は通った
- verifier が Playwright で、`BG_SAMPLES_DIR` あり・なしの 2 つのサーバーの最初の画面を読み出した。ありは `photo-note` が非表示・`photo-note-keep` が表示、なしは逆。食い違いなし（`archives/agents/TODO-165/verifier-report.md`）
- マージ後のローカルホスト（analyzer 0.90.2、r0.28.0、commit 2a0a1b5）で、`photo-note` は hidden、`photo-note-keep` が表示され、文字列も新しい文。期待どおり

## 残ること

- 「保存しない」にした端末でも最初の画面は「解析すると保存し」と出る（保存されないのに出る向きなので安全側）。仕様どおりとして今のままにした（2026-10-20 ユーザー）
- `/version` の取得が終わるまでの一瞬は「保存しません」が見える。測っていない

## 分担の振り返り

- implementer: 2 つの文を出し分ける実装と版の上げを行った。README の `samples` の説明を取りこぼした
- reviewer: 判定を使い回していること、盤面の画面の文を変えていないことを確かめた。見つけたのは README の取りこぼしと、「保存しない」の端末の文の食い違い（検討）の 2 点
- verifier: 設定あり・なしの 2 つで文が切り替わることを読み出した。「設定なし」側は初期状態のままでも同じ結果になるので、`hidden = !serverKeepsSamples` の分岐を区別できていない、と自分で添えた
- 見込みと食い違いは無かった。トークンの大半は main の cache_read で、項目の小ささに比べて会話の往復が多かった
- 次に同じ規模（HTML と JS で文を出し分ける）をやるなら: implementer の依頼に「該当する仕組みを説明する README を `rg` で探して直す」と最初から書き、reviewer の往復を 1 回減らす。verifier の依頼には、初期状態と同じ結果になる側では区別できない旨を先に書き、`/version` を差し替えて両側を動かす測り方を指定する
