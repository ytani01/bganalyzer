# TODO-114 reviewer の報告

対象: `git diff`（CLAUDE.md・TODO.md・analyzer/test_collected.py・docs/raspi.md・recognizer/collected.py・samples/CREDITS.md）と未追跡の `recognizer/import_collected.py`。
push・PR の作成・`run()` の実行はしていない。読んだのは `gh api` での設定だけ。壊して確かめた変更はすべて元に戻した（バックアップと `diff` で確かめた）。

## 要修正

### 1. `recognizer/collected.py:90-91` 取り込みが開発機に限られていない
- 何が起きるか: `bganalyzer.service` は Pi と開発機の両方で `BG_SAMPLES_DIR` を設定している（`bganalyzer.service:10`）。だから、このコミットを `git pull` した Pi でも、読み違いがあれば `import_collected.run` が `git fetch`・`push`・`gh pr create`・`merge` まで進む。決まっていたのは「動かすのはこの開発機（LAN だけ）」（TODO.md の TODO-114）で、コードにはそれが書かれていない（環境変数や設定での切り替えが無い）。Pi は Funnel で公開されているので、Pi で動くと、誰でも送れる写真がマージまで自動で公開に入る。
- 実害は未確認: Pi に push できる認証情報や `gh` のログインがあるかは確かめていない。無ければ push で `CalledProcessError` になって止まる（worktree とブランチは `finally` で消える）。

### 2. `recognizer/import_collected.py:59-66` 送った人の truth.json の、決まっていない項目までそのまま公開される
- 何が起きるか: `collected.valid`（`collected.py:35-46`）は、決まった項目の型を見るだけで、ほかの項目は弾かない。`add` は `image` と `note` だけを書き換えて、残りをすべて `samples/collected-*.truth.json` に書く。サーバー（`analyzer/samples.py:56-69`）も、受け取った dict をそのまま保存している。
- 実測: `screen1.truth.json` に `"spam": "https://example.com/ad ..."` を足した組は、`valid` が True を返し、`add` のあと `samples/collected-aaa.truth.json` に `spam` が残った（`archives` には入れていない。手元の scratchpad で試した）。
- ブランチ名・コミットメッセージ・PR 本文・ファイル名に入るのは、時刻と `sample_id(name)` だけ。`name` は `collected.NAME`（`user-[A-Za-z0-9-]+`）とサーバーの `SAMPLE_ID` を通っているので、そこに truth.json の中身は入らない。入るのはファイルの中身だけ。
- 書き込む項目を、今の `samples/collected-*.truth.json` の項目（`image, note, corners_TL_TR_BR_BL, home, bottom_colour, points, bar_white, bar_black, off_white, off_black, dice, cube, read, fixed_points`）に絞るかどうかは判断が要る。

### 3. `recognizer/import_collected.py:61-63` 読めない写真が 1 つあると、それ以後の取り込みがすべて止まる
- 何が起きるか: 写真が画像として読めないと、`collected.misreads` は `["読めなかった"]` を返す（真なので `wrong` に入る）。`pick` はそれを選び、`add` の `cv2.imread` が None を返して、`paint` で `AttributeError` になる。すると `run` 全体が例外で終わる。読み違いのある組は `collected/` から消えないので、その組が古い順の 10 組に入っている間は、次の測り直しでも毎回同じところで落ち、何も取り込まれない。
- 実測: `b"not an image"` を `.png` にした組で、`misreads` は `['読めなかった']`、`add` は `AttributeError: 'NoneType' object has no attribute 'shape'` で落ちた。
- 送るのは誰でも（Pi）か、LAN の端末（開発機）。壊れた送信でも起きる。

### 4. `recognizer/import_collected.py:107-108` マージしたあとの `git push --delete` は毎回失敗する
- 何が起きるか: このリポジトリは `delete_branch_on_merge: true`（`gh api repos/{owner}/{repo}` で読んだ）なので、`gh pr merge` の時点で GitHub がブランチを消す。そのあとの `git push origin --delete` は「remote ref does not exist」で終了コードが 0 でなくなり、`check=True` なので `CalledProcessError` になる。マージは済んでいるのに、`run` は例外で終わり、`measure.log` にトレースバックが残る（`finally` は動くので worktree とローカルのブランチは消える）。
- 実害は未確認: GitHub がブランチを消すのが遅れて、`push --delete` が間に合うこともありうる。手元で push はしていない。
- 2 行とも消せばよい（作り込みすぎの節にも書いた）。

## 検討

### 5. `recognizer/import_collected.py:103-104` PR を残したままだと、次の取り込みで同じ組の PR がもう 1 つできる
- 何が起きるか: `pick` が「入っているか」を見るのは `origin/main` の worktree の `samples/` だけ（`:87`）。checks が落ちて開いたまま残った PR、マージが失敗した PR（下の 6）、途中で止まった PR（下の 7）の組は main に入っていないので、次の測り直しでまた選ばれ、同じファイルを入れた PR が新しくできる。どちらかをマージすると、もう片方は衝突する。
- 決めたことは「落ちたら残す」までで、残った PR があるときにどうするかは決まっていない。判断が要る。

### 6. `recognizer/import_collected.py:81-105` マージの直前に main を取り込んでいない
- 何が起きるか: ブランチは最初の `fetch` の時点の `origin/main` から作られ、checks を待つ間（数分）に main が進んでも、取り込まずに `gh pr merge --merge` する。`CLAUDE.md` の「共同開発」は「マージの直前に最新の main を取り込み、`test` が通ってからマージする」と決めている。ほかの PR が `accuracy_baseline.json` を書き直していれば衝突して「not merged」で残り（上の 5 になる）、衝突しなくても、新しい認識で測っていない基準が main に入りうる。衝突したときは `import.log` に書くだけで、ユーザーには知らせない（同じ節の「ぶつかったらユーザーに報告する」）。
- 実害は未確認（main が途中で進む場面は試していない）。

### 7. `recognizer/import_collected.py:82-111` サービスの再起動で止まると、worktree・ブランチ・開いた PR が残る
- 何が起きるか: 取り込みは `uvicorn` の子プロセス（`samples.py:84`）の中で、checks を数分待つ。`bganalyzer.service` は `KillMode` を書いていないので、再起動すると子プロセスも SIGTERM で止まる。Python は SIGTERM では `finally` も `TemporaryDirectory` の後始末もしない。そのため `/tmp` の worktree、`.git/worktrees/` の登録、ローカルの `claude/collected-import-*` が残る。PR を作ったあとなら、マージされないまま開いて残る（上の 5 になる）。開発機の `.git/hooks/post-merge` は、main を `git pull` するたびに `systemctl --user restart bganalyzer` を実行するので、起きる機会は多い。
- 実害は未確認（止めて試してはいない）。

### 8. `recognizer/import_collected.py:98-101` `gh pr create` の失敗を見ていない
- 何が起きるか: `gh` は `check=True` ではなく、`returncode` も見ていない。失敗すると `url` は空のまま `": collected-..."` と記録し、30 秒待って `gh pr checks ""` が失敗し、「checks failed, left open」と記録する。実際には PR は無く、push したリモートのブランチだけが残る。`import.log` を読んでも、何が起きたか分からない。
- `gh pr checks ""` が空の引数をどう扱うかは未確認。

### 9. `recognizer/import_collected.py:23-25` 末尾の部分が同じ別の id が、同じ `collected-<id>` に上書きされる
- 何が起きるか: `sample_id` は最後の `-` より後ろだけを使う。`user-2-x-zzz` と `user-3-y-zzz`（写真は別）は、どちらも `pick` で選ばれた（実測: `['user-2-x-zzz.truth.json', 'user-3-y-zzz.truth.json']`）。そのあと `add` が `collected-zzz` を 2 回書くので、先の組は消え、コミットメッセージと PR 本文には `collected-zzz` が 2 回載る。末尾が `-` の id（`SAMPLE_ID` は許す）では `sample_id` が `''` になり、`collected-.png` になる（実測）。
- PWA の id は `Date.now()-<6 文字>`（`analyzer/static/history.js:76`）なので、ふつうはぶつからない。ぶつかるのは、手で id を作って送ったときだけ。

### 10. 文書が新しい動きに合っていない（差分に入っていないもの）
- `README.md:179`: 「写真は…保存はしません。例外は…Pi の `collected/` に保存します」とだけ書いてある。保存した写真が、読み違えると公開リポジトリに自動で入ることは書いていない。アプリの中の説明（`analyzer/static/index.html:226`「写真と盤面の修正結果をサーバーに保存するようにすると、読み取りの改善に役立ちます」）も同じ。保存するのが既定（TODO-112）なので、アプリを使う人は、写真が公開されると知らないまま送ることになる。アプリの文言を変えるなら analyzer の版も上がる。どこまで書くかは判断が要る。
- `docs/raspi.md:190`・`:216`: 「今の認識で測る」「すぐに測るときは」の `collected.py collected --force` を手で実行しても、今は PR の作成とマージまで進む。表と本文には `report.md` を書くことしか書いていない。
- `recognizer/README.md:661`: 道具の一覧に `import_collected.py` が無く、`collected.py` も「測り直し、消す」だけになっている。
- `analyzer/README.md:271`: `/samples` のあとの流れが「測り直して消す」で終わっている。
- `docs/HANDOVER.md:25-27`: 「`samples/` に入れる前に顔・第三者のものを隠す」が、新しい決まり（盤の上のものはそのまま公開）と食い違う。
- `samples/CREDITS.md:30-31`: 自動で入る写真も「ユーザーが…集めた写真」としているが、開発機にも Pi にも、ユーザーでない人が送れる（LAN か公開か）。誰の写真かを書けるか、どう書くかは判断が要る。

### 11. `CLAUDE.md:42-45` 「人の顔や第三者の投稿は隠してから入れる。」が太字のまま残り、そのすぐ後に「そのまま公開される」が続く
- TODO-114 では「この形に合わせて書き直す」と決めていたが、元の決まりは書き直されず、新しい文が後ろに足されただけ。決まりが 2 つ並んで食い違って読める。さらに、元の決まりを説明していた「screen2 は…」の文が、足した文の後ろへ離れた。

### 12. `analyzer/test_collected.py:74-89` 「同じ名前」と「取り込んだ組の写真」の判定を、それぞれ消しても落ちない
- 実測（1 か所ずつ壊して `uv run pytest analyzer/test_collected.py` を実行した）:

  | 壊したところ（`import_collected.py`） | 結果 |
  |---|---|
  | `seen.add(h)` を消す | 落ちる |
  | 古い順の並べ替えを消す | 落ちる |
  | `len(out) < MAX` を消す | 落ちる |
  | `samples/` の写真の sha を `seen` に入れない | 落ちる |
  | `not added(n)` を消す | **通る** |
  | `seen \|= …`（取り込んだ組の写真）を消す | **通る** |
  | `paint` で塗らない／内側を塗る | 落ちる |
  | `t["image"]` を書き換えない | 落ちる |
  | `collected.py` の `if wrong:` を `if False:` | 落ちる |
  | `to_samples` に `left`（全部）を渡す | 落ちる |

- 理由: `add` の後の `pick`（`:86`）では、bbb は id と写真の両方で除かれるので、片方を消しても結果は変わらない。aaa も、`MAX=1` で ccc が先に選ばれるため、本当に除かれたかは確かめられていない（コメントには「aaa is its photo」とある）。
- `table_row` と `ROW` は試していない。`ROW.sub` は合う行が無くても何も言わずに進むので、README の行の書き出しが変わると、表が書き直されないまま PR になる。

## 好みの範囲

### 13. `docs/raspi.md:204-205` mermaid の分岐 E に「いいえ」の辺が無い
- 隣の B には「いいえ → 何もしない」がある。

## 作り込みすぎ

- `recognizer/import_collected.py:107-108`: delete: マージのあとの `git push origin --delete`。リポジトリの `delete_branch_on_merge` が同じことをする。要修正 4 と同じ箇所（重さは要修正）。
- `recognizer/import_collected.py:114-117`: shrink: `__main__` と `collected.to_samples`（`collected.py:95-99`）が、`import.log` を開いて時刻を付ける処理を 2 回書いている。片方からもう片方を呼べば 3 行減る。好みの範囲。

net: -5 lines possible.

## 問題の無かった観点

- 10 組まで・古い順（truth.json の mtime）・`samples/` と同じ写真（そのまま送られたもの）の除外・同じ id の除外: 決めたとおり（ただし 12 のとおり、テストは片方しか見ていない）。
- 盤の外を黒く塗る・写真の大きさと四隅を変えない・EXIF を入れない（`cv2.imwrite` は EXIF を書かない）: 決めたとおり。テストで塗りと大きさを見ている。
- 基準（`check_accuracy.py --update`）と README の「精度」の表の書き直し: worktree の中で行っている。今の README の行（「Pi に集めた写真 17枚」）にも `ROW` は合う。
- 別の worktree: 作業中のチェックアウトに触るのは `fetch`・`worktree add/remove`・`branch -D` だけで、作業ツリーとインデックスは変えない。
- `collected/` のデータ: 取り込みは `collected/` を読むだけで、消さない。
- テストから本当に push されないか: `analyzer/test_collected.py` の autouse の fixture が `to_samples` を差し替え、`analyzer/test_api.py` の `/samples` のテストは `Popen` を差し替えている。
- バージョン: `import_collected.py` は読み取りの結果を変えない道具なので、recognizer の版を上げないのは `CLAUDE.md` の「バージョン」どおり。
- CI: samples だけの PR でも `test`（`paths-ignore` は md・docs・archives）と `accuracy`（`samples/**`）が走る。
- コメント: 「なぜ」が書いてある（`:91` の venv、`:105` の `--delete-branch`）。
- 範囲: 指示に無い変更は無い（`samples/CREDITS.md` の「Pi に残す」を「サーバーに保存する」に直したのは、同じ段落の更新の中の直し）。
