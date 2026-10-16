# TODO-082 reviewer の報告

対象: `git diff`（12 ファイル）と未追跡の `analyzer/claude_corners.py`。設計は `design.md`。
実測は scratchpad に置いた偽の `claude`（Python）だけを使った。本物の `claude` は 0 回。
`uv run pytest analyzer/test_api.py -k claude -q` → 3 passed。

## 直すべき

### 1. `analyzer/claude_corners.py:64-70` claude が先に終わると、残った子を殺さない

`_kill` は `proc.returncode is None` のときだけ `os.killpg` する。claude 本体が終わって、
同じグループの子が残っている（stdout を握っている、または握っていない）とき、グループを殺さない。

- 実測: 偽の claude が `sleep 30` を起動して（stdout を引き継ぐ）すぐ `exit 0` → `communicate()` は
  子が pipe を閉じるまで終わらず、`TIMEOUT=2` で 504。そのあと **`sleep 30` が生きていた**。
  `BaseSubprocessTransport.__del__` の `Event loop is closed` も出た（pipe が開いたままの transport が残っている）
- 成功した場合（pipe を閉じた子が残る場合）も同じく殺さない
- 今の `claude` がこう振る舞うかは未確認（実害は未確認）。ただ、設計の「グループごと殺し、残さない」とは合わない
- `returncode` を見ずに `killpg` すれば足りる（メンバーが居なければ `ProcessLookupError` で、既に拾っている。
  Linux はグループ ID として使われている PID を再利用しない）。テストは今の `slow` と同じ作りで 1 本足せる

### 2. `analyzer/claude_corners.py:58-59,125` 返事の `NaN` が 500 になる

`json` は `NaN` を受け付け、`float(x)` を通り、`min(max(nan, 0), w)` も `nan` のまま返る。
Starlette の JSONResponse は `allow_nan=False` なので応答を作るところで落ちる。

- 実測: 偽の返事 `{"corners": [[NaN, 10], ...]}` → **500**（`_running` は戻った）。
  `1e400`（`inf`）は `w` に収められて 200
- 公開サーバーで受け取る値の検査なので、`math.isfinite` で弾いて 502 にするのがよい

## 直すとよい

### 3. `CLAUDE.md:32-37` 写真の扱いの文面が食い違う

- 1 文目が「**例外は**〜ときだけ」のままなので、足した「もう 1 つの例外は」と矛盾する
- 元の行末「`collected/` はリポジトリに自動では入れない」に句点が無く、次の行と続けて表示される
  （「入れないもう 1 つの例外は」）
- 見出しの決まりは「保存しない」で、Claude の例外は「外へ送る」話。「保存しない」の例外として並べると
  何の例外か分かりにくい。「保存もせず外へも送らない」のように 1 文目を広げるかどうかは main の判断

### 4. `docs/raspi.md:114-115` リポジトリの `bganalyzer.service` を書き換えさせている

手順 2 は、Git で管理している `bganalyzer.service` の `#` を外させる。そうすると作業ツリーが汚れ、
上流がこのファイルを変えたときに `git pull` が止まる。103-105 行の「`bganalyzer.service` が変わったら
`sed` からやり直す」をすると、自分の書き換えも毎回やり直しになる。開発機にも同じ常駐を入れてある
（メモリ）ので、そちらも同じ。

- `systemctl --user edit bganalyzer`（`~/.config/systemd/user/bganalyzer.service.d/override.conf` に
  `[Service]` `Environment=BG_CLAUDE=%h/.local/bin/claude`）なら、`sed` のやり直しで消えない
- `bganalyzer.service:12` のコメントの `/home/<ユーザー>/` も、ユーザー unit なら `%h` で書ける

### 5. `README.md:43-49,80-86` ルートの README のモジュール構成に `claude_corners.py` が無い

mermaid の図（`app.py` のエンドポイントの一覧、`samples.py` の箱）と、ファイルの表
（`analyzer/models.py`, `samples.py` の行）の両方。`/claude-corners` も図のエンドポイントの一覧に無い。

### 6. `docs/PI_CHECKS.md:101-103` 取り消しを Funnel 越しに確かめていない

- 実測: uvicorn を直接立てて（127.0.0.1:8765）偽の `slow` に `curl --max-time 2` → 2 秒で 499、
  偽の claude と子が両方消えた。続けた 2 本目も 429 にならず起動した（`_running` が戻っている）
- PI-049 の確かめ方も `http://127.0.0.1:8000/` で、Tailscale Funnel を通らない。スマホの利用は Funnel 越しで、
  ブラウザの中断が Funnel から uvicorn までの接続を切るかは未確認（実害は未確認）。
  スマホの行で取り消したあとに、Pi の Claude が `pgrep -af claude` を見る形にするかは main の判断

### 7. `analyzer/claude_corners.py:5,80` 「利用枠を食われないように」は同時 1 本では守れない

同時は 1 本でも、終わるたびに次を送れば 1 回 7〜9 秒で続けて呼べる（1 時間に数百回）。
docstring は「don't let anyone use up the owner's limits」と書いている。同時 1 本はユーザーが決めたことなので、
回数の上限を足すか、docstring と `docs/raspi.md:119` の書き方を実態に合わせるかは判断が要る。

### 8. `analyzer/static/app.js:778-779` Claude で置き換えたあとも `cornersFixed` が残る

`claudeCorners` は 4 つとも置き換えるが `cornersFixed` を戻さない。前にドラッグした隅があると、
そのあとの「もう一度検出」は、その位置の **Claude の点** を「ユーザーが置いた隅」として固定して送る
（`findAgain` の 737 行）。意図どおりかは判断が要る（実害は未確認）。

### 9. `analyzer/claude_corners.py:93-97` `BG_CLAUDE` のパスが間違っていると 500

`create_subprocess_exec` の `FileNotFoundError` / `PermissionError` を拾っていない（未実測。コードを読んだだけ）。
`_running` は外側の `finally` で戻る。PWA には「Internal Server Error」が出る。手順 2 でパスを手で書く設定なので、
502 と短い理由にしておくと Pi での切り分けが早い。

### 10. `analyzer/test_api.py:785-794` 終了コード 0 以外 → 502 と、切断の道にテストが無い

実装の報告にあるとおり。切断は TestClient では起こせないので、上の 6 の実測と PI-049 で見る形でよい。
1 の「本体が先に終わる」も今のテストでは捕まらない（`slow` は本体が生きたまま）。

## 問題の無い観点

- 時間切れ: `slow` の偽で 504、本体と子の pid が消える、`_running` が戻る（テストが確かめている）。
  `killpg` を `proc.kill()` にすると落ちることは実装の報告どおり
- `CancelledError`: `finally` で `reply.cancel()` と `_kill` を通る。Starlette は切断で handler を cancel しないので、
  0.5 秒ごとの `is_disconnected()` が要る作りは正しい
- 429 の判定と `_running = True` の間に `await` が無い（取り合いが起きない）。失敗・取り消し・500 のどれでも戻る（実測）
- 画像の大きさ: 送る前に長辺 1568px に縮める。受け取る量に上限が無いのは `/find-corners`（`app.py:203`）と同じ
- ログ: 開始（モデル・幅・高さ）と結果（秒数）だけ。写真・返事の本文は出していない。502 の `from e` もログに出ない
- PWA: 取り消しで `AbortError` を知らせない、`search` の番号・写真・点の動きを見てから置く、縮尺は `uploadImage` の
  `scale` で戻している（`findAgain` と同じ）。ボタンと注意は `/version` の `claude` でだけ出る（`[hidden]` は `!important`）
- 版: analyzer 0.48.0 → 0.49.0（機能の追加）、`APP_VERSION` も 0.49.0。recognizer は変えていない
- `analyzer/README.md`・`/version` の例・PI_CHECKS の件数と次の番号（`archives/pi/` は 47 件）は実装と合っている
- 範囲: 指示に無い変更は無い

## 作り込みすぎ

- `claude_corners.py:100-103`: shrink: `while not reply.done():` と中の `if reply.done(): break` が重なっている。
  `while not (await asyncio.wait({reply}, timeout=0.5))[0]:` の 1 行に
- `claude_corners.py:112-113`: shrink: 終わった Task の `cancel()` は何もしないので `reply.cancel()` だけでよい
- `claude_corners.py:65`: delete: `if proc.returncode is None:`（上の 1 を直すと消える）
- `app.js:1025`: delete: `e.stopPropagation()`。`#busy` の click を聞くのは読み取り中（`recognize`）だけで、
  そのとき「取り消す」は出ない
- `claude_corners.py:125`: yagni: 応答の `width`・`height` を PWA は使っていない。設計どおりなので好みの範囲

net: -5 lines possible.
