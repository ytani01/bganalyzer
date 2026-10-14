# TODO-038 reviewer の報告（2 回目）

対象: `git diff 2b7c25b..96d2319`（全体は `c19c1c8..HEAD`）。コードは直していない。claude -p 関連の前回の指摘は対象外。

実測の方法: `samples/screen1` を `user-*` の名前で scratchpad に複製し、truth だけ書き換えて
`uv run -q --no-project --python 3.12 --with opencv-python-headless --with numpy python recognizer/collected.py <dir> --force` を走らせた。
pydantic の `list[int]` が何を受け付けるかは、`uv run --with pydantic` で `Board` と同じ定義を作って確かめた。

## 要修正

なし。

## 検討

### 1. evaluate.py をそのまま collected/ に使うと、前回の要修正 3・4 がまだ起きる

- 場所: docs/raspi.md の表「今の認識で測る」（`python recognizer/evaluate.py /data/samples/*.truth.json`）、recognizer/evaluate.py の `__main__`
- 内容: collected.py は直ったが、evaluate.py のコマンドライン版は truth の `cube['at']` と `dice` をそのまま表示し、`"cube": "x"` の組では
  `TypeError` で止まる（前回の実測と同じ行で、今回は変えていない）。docs/raspi.md には「認識を直すのは、Pi の Claude Code に
  『collected の report を見て直して』と頼んだとき」とあるので、Pi の Claude がこの表のコマンドで collected/ を測る見込みが高い。
  人が見ている場面なので重さは下がるが、「正解の中の文字を出さない」は collected.py の中だけで成り立っている。
  同じ表の `grep -o '"fixed_points'...` も truth を直接読む。

### 2. テストを壊しても落ちない所

- analyzer/test_collected.py:48-56 — `valid()` を消しても通る。`cube={"at": "IGNORE..."}` と `cube="x"` の組は、`valid()` が無くても
  `evaluate.run` が例外を出さず「キューブ」の読み違いとして `## user-bad.truth.json` に載り、`"user-bad.truth.json" in report` も
  `"IGNORE" not in report` も成り立つ（今の report.md は truth の文字を出さない作りなので）。
  `valid()` が実際に要るのは points の型: `save_sample` の `Board`（pydantic、`list[int]`）は `5.0` や `True` を受け付け
  （実測。`points=[5, ...]`・`bar_white=1` に変換して通る）、保存するのは変換前の `t` なので、truth に `5.0` が残る。
  そのポイントを読み違えると collected.py:58 の `f"{a:+d}"` が `ValueError: Unknown format code 'd' for object of type 'float'`
  になる（format の部分だけ実測）。この行は `try` の外。`valid()` の `type(n) is int` がこれを防いでいるが、それを確かめるテストが無い。
  「正解の形が違う組」の節に入ったかどうかを見るか、points に `5.0` を入れた組を足せば落ちるようになる。
- analyzer/test_api.py:513-532 — `Running.poll()` が常に `None` なので、「前の測り直しが終わったら次を起動する」は見ていない。
  `if _measuring: return` のように二度と起動しない形にしても通る。

### 3. 子プロセスの失敗が見えない

- 場所: analyzer/app.py:202-203
- 内容: `stdout`・`stderr` とも `DEVNULL` なので、collected.py が途中で落ちても、どこにも残らない。落ちると `.measured.json` が
  書かれないので、新しい組が 10 以上のまま、次に保存するたびに全部の組の測り直しが起動し直す（同時に 1 つまでなので暴走はしない）。
  `stderr` をサーバーのログ（コンテナのログ）に流すかどうか。

### 4. 公開の POST で、測り直しを何度でも起こせる

- 場所: analyzer/app.py:197-203、recognizer/collected.py:74
- 内容: 新しい組を 10 送るたびに、collected/ の全部の組（最大 1000）を測り直す。読み違いの組は消えないので、送るほど 1 回が長くなる。
  測っている間は API と同じコンテナで CPU を使い、gnubg の解析は 60 秒で打ち切る（analysis.py:241）ので、遅くなれば
  `/analyze` が失敗しうる（未確認。Pi で 1 組を測る時間も測っていない）。1000 組で保存は止まるので無限ではない。
  `os.nice` などで優先度を下げるかどうか。
- 20 MB までの画像なので、展開すると大きくなる PNG で子プロセスのメモリを使い切れるか（未確認）。これは `/analyze-photo` にも前からある。

### 5. `measure_collected` の例外で `save_sample` が 500 になる

- 場所: analyzer/app.py:190
- 内容: 保存のあとで呼ぶので、`Popen` の `OSError`（プロセスやメモリが足りないとき）は、組を保存できたのに 500 を返す。
  `new_pairs` は `.measured.json` が壊れていても `OSError`・`ValueError` を受けるので、ここからはまず出ない
  （`.measured.json` は collected.py しか書かない）。起こりにくいので報告だけ。

### 6. 手で走らせた `--force` と、サーバーが起動したものが同時に動く

- 場所: docs/PI_CHECKS.md の PI-019、docs/raspi.md「すぐに測るときは…」、analyzer/app.py:197
- 内容: `_measuring` はサーバーが起動したものしか見ない。2 つが同時に同じ組を消すと、後の方は `glob` で見つけたファイルの
  `unlink`、または `stat`（collected.py:75）で `FileNotFoundError` になって止まる（コードから。実測はしていない）。
  先に終わった方の report.md は残る。

### 7. analyzer/README.md の `POST /samples` に、測り直しと削除が書かれていない

- 場所: analyzer/README.md:158-163
- 内容: 保存のたびに新しい組を数え、10 以上で子プロセスを起動すること、読み違いの無い古い組が消えることが書かれていない。
  保存したファイルが後で消えるのは API の挙動の変化。

### 8. 前回の検討 11（測っている間の上書き）は形を変えて残る

- 場所: recognizer/collected.py:74-78
- 内容: 測り直しは保存をきっかけに始まり、保存と並んで動くので、前回より起きやすい。ただし mtime は全部を測ったあとに取るので、
  測っている間に送り直された組は一番新しい扱いになり、消されない。消されるのは `stat` から `unlink` までの短い間に送り直された組だけ。
  その組の report.md の判定は古い中身のもの。

## 好み

- analyzer/app.py: 測り直しを起動したことをログに出していない。report.md の時刻でしか分からない（PI-019 もその見方）。

## 前回の指摘で、今の形で残るもの

| 前回 | 今 |
|------|----|
| 要修正 3（truth の文字が出る） | collected.py の report.md では解消。出るのは名前（`user-[A-Za-z0-9-]+` に限っている）、固定の文字、整数だけ。evaluate.py は残る（検討 1） |
| 要修正 4（公開の POST で落ちる） | collected.py では解消。実測: 四隅が NaN の組は「読めなかった」、1e12 や画像の外の四隅は読み違いとして載り、どれも落ちない。evaluate.py は残る（検討 1） |
| 検討 7・9 | cron と一緒に無くなった |
| 検討 11 | 残る（検討 8） |
| 検討 12 | HANDOVER.md の食い違いは解消（自動で反映しなくなった）、recognizer/README.md に collected.py が入った。analyzer/README.md が新たに足りない（検討 7） |
| 検討 13 | エラーの組と送り直した組のテストが入った。壊しても落ちない所が残る（検討 2） |

## 問題の無かった観点

- ゾンビ: 終わった子プロセスは、次の保存のときの `poll()` で回収する。残っても 1 つまで。
- 並行: サーバーは 1 ワーカーで、`_measuring.poll() is None` の間は起動しない（テストもこれは見ている）。
- gnubg の子プロセス: `ProcessPoolExecutor`（spawn）で別に管理しており、`SIGCHLD` の扱いも無いので、`Popen` とは干渉しない。
  collected.py は `import evaluate` を測るときにだけ行い、gnubg を読まない。
- 応答を止めるか: async の `save_sample` から同期で呼ぶが、やるのは `glob` と `.measured.json` の読み込み、`Popen` の起動だけで、待たない。
- `valid()`（evaluate.run が読む欄）: image・corners・home・points・bar・dice・cube は見ている。`bottom_colour` は真偽だけで使うので型は要らない。
  `url` は見ていないが、evaluate.run が使うのは画像が無いときだけで、`save_sample` は truth より先に画像を書くので届かない。
  cube の `at` の値（white・black・centre）は cube.py と sample.js に合っている。
- バージョン: analyzer 0.26.0（機能の追加）と `APP_VERSION`、recognizer 0.8.0 は CLAUDE.md どおり。sw.js の CACHE も上げてある。
- docs/raspi.md・docs/PI_CHECKS.md・TODO.md・CLAUDE.md（例外の削除）は今の実装と合っている。

## 作り込みすぎ

作り込みすぎ: なし。`valid()` は消せそうに見えるが、points の `5.0` を止めているので要る（検討 2）。

Lean already. Ship.
