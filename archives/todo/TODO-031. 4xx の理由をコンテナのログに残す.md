# TODO-031. 4xx の理由をコンテナのログに残す

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort low | main（実装）+ reviewer（Opus / high）+ verifier（Sonnet 5.5 / medium） |
| 実施 | Opus 5.5 / effort low | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Sonnet 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | low | 38 | 7,933 | 21,584 | 1,572,275 | 75% |
| reviewer | Opus 5.5 | high | 30 | 177 | 46,905 | 489,544 | 25% |
| 合計 |  |  | 68 | 8,110 | 68,489 | 2,061,819 | 計 2,138,486 |

- verifier は定義のモデルが haiku。実測（壊して落ちるか、実際のログ）が要るので Sonnet 5.5 に上書きした。effort は定義の medium
- verifier は終点のコミット（38d80a3）のあとに動いたので、`token-usage.py` の範囲に入っていない。
  Agent ツールの通知では 28,080 トークン
- reviewer の output が 177 と小さいのは、`subagents/` のログに最終行が残らない分（todo-workflow skill）と思われる

## きっかけ

2026-10-14、スマホで写真の読み取りが失敗した。コンテナのログには `POST /analyze-photo ... 422` しか残らず、理由が分からなかった。

## やったこと

- `analyzer/app.py` に例外ハンドラーを 2 つ足し、`uvicorn.error` のロガーに理由を 1 行出す。
  - `HTTPException` の 4xx: メソッド、パス、ステータスと detail。detail には送られた値（局面の ID）が入ることがあるので、
    `%r` で 1 行に収める（改行でログに偽の行を作らせない）
  - `RequestValidationError`（フォームの検証）: 項目の場所とメッセージだけ。入力値（`input`）は出さない
  - レスポンスは FastAPI の既定のハンドラーに任せ、前と変えない
- テスト `test_4xx_reason_is_logged` を足した
- analyzer を 0.25.1 に上げた（`APP_VERSION`、sw.js のキャッシュ名も）。main の 0.25.0（Pi に残す）とぶつかったので取り込んで付け直した
- マージ後に Pi で確かめる PI-016 を足した（main の PI-015 とぶつかったので付け直した）

## 確かめたこと

- reviewer: 11 通りのリクエストで、レスポンス（ステータス・本文・ヘッダー）が前と同じ。テストが入力の漏れを捕まえられないと指摘され、直した
- verifier: pytest は git の無いイメージで必ず落ちる 1 件を除いて通る。`input` をログに出す、`%r` を `%s` にする、ログ行を消す、の 3 通りでテストが落ちる。
  実際のコンテナのログに `POST /analyze-photo -> 422: 'could not decode image'` と
  `body.plies: Input should be a valid integer, ...` が出て、送った値は出ない

## 残ること

- 静的ファイルやルーティングで返る 404 / 405 はログに出ない（Starlette の `HTTPException` はこのハンドラーを通らない）。
  ボットのアクセスでログが埋まるので外したままにした
- Pi のログに出るかは PI-016 で確かめる

## 分担の振り返り

- reviewer は、テストが入力の漏れを捕まえられないこと、detail の改行でログに偽の行を作れること、404 / 405 が対象外なことを見つけた。
  verifier は食い違いを見つけなかった
- 見込みどおりの編成で動いた。main の取り込みで版と番号を付け直したのは、立てる前に `git fetch` していなかったため
- 次に同じ規模（1 ファイルの小さな挙動の変更）なら同じ編成でよい。着手前に `git fetch` して main の版と番号を見ておく
