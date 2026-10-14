# verifier-report TODO-036

1. 実装が効いている: OK。終了コード 0。
   - `OK   export: files=[...png, ...truth.json] points_match=True dice=[4, 2] alerts=[]`
   - `OK   export-denied: files=[...png, ...truth.json] points_match=True dice=[4, 2] alerts=[]`
2. 壊すと落ちる: OK。export-sample の share 部分を 44e9ec1 の形（AbortError 以外を throw）に戻して再ビルド。
   - `OK   export: ... alerts=[]`
   - `FAIL export-denied: files=[] points_match=False dice=None alerts=['書き出せませんでした: Permission denied']`
   - 終了コード 1。
   - 復元: `git checkout analyzer/static/app.js` と再ビルドのあと、export と export-denied が両方 OK、終了コード 0。
     `git status --short` は `?? archives/agents/TODO-036/` のみ。
3. pytest: `8 failed, 32 passed, 6 skipped`。
   - イメージに pytest が無く、コンテナ内の /tmp/pt に `pip install --target` で入れて実行した（リポジトリは無変更）。
   - 落ちた 8 件:
     - `test_version_reports_both_parts_and_commit`: `FileNotFoundError: 'git'`（既知）。
     - 残り 7 件: `/app/samples/*.truth.json` が無い `FileNotFoundError` が 6 件、`test_api_find_corners` は `AttributeError: 'NoneType' object has no attribute 'shape'`（サンプル画像が読めないためと推定）。
       イメージに samples/ が入っていないため。
   - 8 件とも差分と関係なさそうだが、サンプルのあるクローン上では走らせていないので、依頼の「それ以外が通るか」は **通ったとは言えない**。

補足: 1 回目の /version の commit は 44e9ec1 だった（その時点のビルドが古いコミットのラベルで焼かれていた）。
app.js の差分は APP_VERSION 0.25.3 で、動作は新しい版だった。
