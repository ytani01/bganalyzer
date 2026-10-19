# TODO-176. 盤面の画面で、盤の横の元の写真には写真だけを出す

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort high | implementer（Sonnet 5.5 / medium）+ reviewer（Opus 5.5 / high。描き分けの分岐が変わるので入れ、先に回す）+ verifier（Sonnet 5.5 / medium。live_view の画面で `BG_CDP` を付けて確かめる） |
| 実施 | Opus 5.5 / effort high | implementer（Sonnet 5.5 / medium）+ reviewer（Opus 5.5 / high）+ verifier（Sonnet 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main + reviewer | Opus 5.5 | high | 52 | 7,503 | 49,766 | 1,687,197 | 64% |
| implementer + verifier | Sonnet 5.5 | medium | 60 | 9,293 | 81,968 | 893,865 | 36% |
| 合計 |  |  | 112 | 16,796 | 131,734 | 2,581,062 | 計 2,729,704 |

- `token-usage.py` は担当ごとの行に分けられず、モデル別の 2 行になった。Opus 5.5 の行は main と reviewer、Sonnet 5.5 の行は implementer と verifier の合計
- effort は `TODO.md` の見込みに書いた値（担当の定義ファイルは無い）

## きっかけ

盤面の画面で盤の横に出す元の写真は、盤の絵と同じ部品で描くので、「◯ ポイントマッチ」、点数、PIP、ゴール（上がりのトレイ）なども一緒に出ていた。写真だけでよい（2026-10-20 ユーザーが決めた）。

## やったこと

- `analyzer/static/board-view.js` の `draw`: 写真があるときは、viewBox を写真の範囲（`PLAY`）だけにして `image` を 1 つ描いて戻る。枠・トレイ・番号・点数・PIP・キューブ・ダイスは出ない。写真があるときにしか通らなくなった `photo` の分岐は消し、冒頭のコメントも直した
- 初めは盤の側と高さをそろえて「◯ ポイントマッチ」の帯の分の空白を残したが、「高さをそろえる必要はない。不要な空白は消して」との指示で、写真の範囲だけの viewBox にした。2 列に並べたとき、写真の側が盤の側の高さに引き伸ばされないよう `analyzer/static/style.css` の `#photo-wrap` に `align-self: start` を足した
- analyzer を 0.94.0 に上げた（`analyzer/app.py`、`analyzer/static/app.js` の `APP_VERSION`）。`analyzer/static/sw.js` の `CACHE` を v61 にした

## 確かめたこと

- reviewer: 要修正なし。盤の側の描き方と描く順は変わらないこと、写真の像が viewBox にぴったり収まり歪まないことを読んで確かめた（`archives/agents/TODO-176/reviewer-report.md`）
- verifier: main（0.93.0）とブランチ（0.94.0）を並べて起動し、盤の側の viewBox・子要素の数・タグごとの数・innerHTML の長さが一致し、写真の側の子要素が `image` の 1 つだけであることを測った（`archives/agents/TODO-176/verifier-report.md`）
- 利用者が画面を見て OK を出した（2026-10-20）
- ローカル（マージ後。2026-10-20）: `git pull` で `bganalyzer.service` が再起動し、`/version` が analyzer 0.94.0 になった。Playwright（1300 幅、保存はオフ）で samples の画面の写真を読み取り、盤面の画面の `photo-svg` の子要素が `image` の 1 つだけ（viewBox `20 24 616 392`）であることを確かめた

## 分担の振り返り

- implementer: 最初は分岐を 1 つ足すだけで済ませ、使われなくなった `!photo` の判定は残した。管理者の指示で消した。見つけたことは「写真があっても `match` が viewBox を広げて、空白の帯が残る」点。これは利用者の判断で viewBox を写真の範囲だけにして解消した
- reviewer: 空の帯が残ることを指摘し、そのあとの直しでは起きなくなったことを確かめ直した。要修正はなかった。コードの差分が小さい項目で、reviewer が実際に防いだ手戻りは無い
- verifier: 盤の側が変わらないことを main との並べ比較で測り、写真の側が `image` 1 つだけであることを示した。食い違いはなかった
- 食い違い: 見込みと担当の構成は同じ。実際の手戻りは、空白を残す案が利用者の確認で変わったことの 1 回で、担当の構成のせいではない
- 次に同じ規模（描き分けの分岐が 1 つ変わる表示の直し）なら、利用者に見せて空白を残すかを先に聞き、決まってから implementer を起こす。reviewer は、描く順が変わらないことを確かめるだけなら implementer の自己確認と管理者の読みで足りる見込みだが、分岐の消し方（動かなくなった判定を残すか）は reviewer が見る価値がある
