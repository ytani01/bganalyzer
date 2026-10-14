# TODO-034 verifier 報告

## 1. 文書のコマンドで全部を 1 回
`uv run -q --no-project --with playwright python tools/pi_ui_check.py` -> 終了コード 0

```
version: {'analyzer': '0.25.2', 'recognizer': '0.7.0', 'commit': '701d757', 'samples': True}
OK   double: dice=[4, 2] best='24/20 13/11' cube-help='ダイスがあるので、最善手を出します。' alerts=[]
OK   speech: spoken=['手前の人、ダイス 4 2の最善手は、8から4、6から4。ほぼ互角です。'] alerts=[]
OK   export: files=['user-20261014-1151.png', 'user-20261014-1151.truth.json'] points_match=True dice=[4, 2] alerts=[]
OK   collect: off=[] on=['user-1791946325054-5nu6ia.png', 'user-1791946325054-5nu6ia.truth.json'] evaluate=['user-1791946325054-5nu6ia.truth.json: 24/24 points correct, bar ok, home guess ok (-18.0), dice ok (read [4, 2], truth [4, 2]), cube not found (read None, truth centre)'] left=[]
```
`collected/` は流す前も後も空（ファイル 0 件、diff 無し）。一致。

## 2. アプリ側を壊すと落ちるか
worktree のコピー（HEAD）の URL を 8001 に変え、`analyzer/` を `/app/analyzer:ro` でマウントした別コンテナで実行。
BG_SAMPLES_DIR なし。壊していないコピーでも `export` は OK（環境のせいではない）。

- (a) speechText の `standingToSpeech(r)` を勝率の数字に置換 -> 期待どおり FAIL
  `FAIL speech: spoken=['手前の人、ダイス 4 2の最善手は、8から4、6から4。勝率 50%'] alerts=[]` exit=1
- (b) cube-help の文を「ダイスがあります。」に変更 -> 期待どおり FAIL
  `FAIL double: dice=[4, 2] best='24/20 13/11' cube-help='ダイスがあります。' alerts=[]` exit=1
- (c) export-sample で truth.json の File を作らない -> 期待どおり FAIL
  `FAIL export: files=['user-20261014-1153.png'] points_match=False dice=None alerts=[]` exit=1
- 壊していないコピー: `OK   export: files=['user-20261014-1153.png', 'user-20261014-1153.truth.json'] points_match=True dice=[4, 2] alerts=[]`

後片付け: 8001 のコンテナは停止済み（`docker ps` は bganalyzer-app-1 のみ）、worktree は削除済み。
本体の作業ツリーは `git status` で変更なし（このレポート以外）。本番のコンテナは触っていない。

## 3. 文書の表とスクリプトの読み合わせ
4 行とも主旨は一致。表に書かれていない細かい判定（食い違いというより省略）:
- `export`: 写真が空でないこと、画像名が truth.json の `image` と一致すること、`home` が正解と同じことも見ている。
- `collect`: 画面の alert が無いことも条件。`evaluate.py` は終了コード 0 だけを見ていて、点数の正しさ（24/24 など）は判定に入っていない。
  上の出力では 24/24 だったが、点数が下がっても OK になる。実害は未確認。
- `double`: 画面の alert が無いことも条件（表には無い）。

## 確かめられなかったこと
- `collect` は指示どおり壊す確認をしていない。
- 実行したコンテナの commit は 701d757（HEAD b4fa37a より古い）。`/version` の commit は .git が古いイメージのため。静的ファイルは HEAD のコピーを使った。
