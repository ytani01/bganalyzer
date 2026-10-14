# TODO-031 reviewer の報告

対象: `git diff fa224c9 HEAD`（6453696）。問題点だけを書く。

確かめ方: 常駐用の `bganalyzer` イメージ（fastapi 0.143.0、uv.lock と同じ）で、fa224c9 の `app.py` と今の `app.py` に
同じ 11 通りのリクエスト（静的ファイルの 404、GET /analyze-photo、position_id の誤り、壊れた JSON、型の誤り、
写真のフォームの誤り、/find-corners に文字列）を送り、ステータス・本文・ヘッダーを比べた。**11 件とも一致**（レスポンスは変わっていない）。
テストの強さは app.py を書き換えて `test_4xx_reason_is_logged` だけを流して確かめた。

## 要修正

### analyzer/test_api.py:440 — 「入力を出さない」ことを確かめていない
- 問題: `"secret-value" not in caplog.text` は、検証エラーの `input` をログに足しても通る。
- 根拠（実測）: `app.py:55` を `f"...: {e['msg']} {e['input']}"` に変えても **1 passed**。
  2 本目のリクエストのエラーは `image` と `corners` の欠落だけで、どちらも `input` は `None`。
  `home="secret-value"` は正しい値なのでエラーに入らず、`input` に載る経路を通らない。
  （`exc.body` を丸ごと出す書き換えでは落ちるので、そちらは守れている。`str(exc.errors())` に変えた場合も落ちるが、
  落ちる理由は `body.image: Field required` の書式が変わったためで、入力が漏れたからではない）
- 入力が `input` に載るのは、型の誤りなどで値そのものが検証に落ちたとき（例: `bottom_colour="SECRET"` →
  `body.bottom_colour: Input should be a valid integer...`、`input` は `"SECRET"`）。

## 検討

### analyzer/app.py:140（と app.py:48）— position_id がそのままログに出る。改行も通る
- 問題: `HTTPException(422, f"invalid position id: {req.position_id}")` の detail をそのまま出すので、
  利用者が送った position_id がログに残る。長さの上限も無く、改行を含めるとログに偽の行を作れる。
- 根拠（実測）: `{"position_id": "SECRETPID\nFORGED -> 200 ok"}` を送ると、ログは次の 2 行になった。
  ```
  POST /analyze -> 422: invalid position id: SECRETPID
  FORGED -> 200 ok
  ```
- 依頼の「入力値はログに出さない」に当たるかは判断が要る（position_id は写真でもフォームでもなく JSON の値。
  CLAUDE.md の決まりは写真の保存についてだけ）。実害は未確認。
- 他の detail は固定の文か、入力から数えた数（`each side needs 15 checkers (white {w}, black {b})` など）で、
  入力そのものは出ていない（app.py:93 経由の analysis.py の ValueError を読んだ）。

### analyzer/app.py:45 — 静的ファイルとルーティングの 404 / 405 はログに出ない
- 問題: 登録しているのは `fastapi.HTTPException` で、Starlette のルーティングや `StaticFiles` が投げるのは
  親クラスの `starlette.exceptions.HTTPException`。そちらはこのハンドラーを通らない。
- 根拠（実測）: `GET /nope.png`（404）と `GET /analyze-photo`（`/` の静的ファイルに落ちて 404）は、
  どちらもログに何も出なかった。レスポンスは前と同じ。
- 静的ファイルの 404 を出さないのが狙いどおりなら問題ない（ログが増えない）。ただ「4xx の理由を出す」と
  書いてあるので、意図して外したのかは確かめた方がよい。PWA の古い端末が消えたファイルを取りに来る、
  といった 404 の理由は今後もログに出ない。

## 好みの範囲

### analyzer/app.py:29 — 版の上げ幅
- CLAUDE.md の「バージョン」は「直しは 0.0.1、機能の追加や変更は 0.1.0」。ログに理由を出すのは
  機能の追加とも読めるが、TODO-031 の「決めたこと」で 0.24.1 と決めてあるので、そのままでよいと思う。
  `APP_VERSION`（app.js）は揃っている。sw.js の `CACHE` を上げるのは過去の版上げ（35dcdd9、2b987a3）と同じ扱い。

## 作り込みすぎ

- `analyzer/app.py:47`: `if 400 <= exc.status_code < 500` は、今のコードに 5xx の `HTTPException` を投げる所が無いので
  効いていない（`rg -n "HTTPException\(" analyzer` は 422 だけ）。消せば 1 行減るが、5xx を足したときの備えとして
  残しても害は無い。好みの範囲。

net: -1 line possible.
