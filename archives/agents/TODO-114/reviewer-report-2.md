# TODO-114 reviewer の報告（2 回目）

対象: 直したあとの `git diff` と `recognizer/import_collected.py`。前の報告は `reviewer-report.md`。
push・PR の作成・`run()` の実行はしていない。`merge()` は、偽の `gh` を渡して手元で動かした。壊して確かめた変更はすべて元に戻した（`diff` で確かめた）。

## 前の指摘はどうなったか

| # | 結果 |
|---|---|
| 1 Pi でも動く | 直った。`BG_IMPORT` が無いと `to_samples` を呼ばない。テストは、条件を外すと落ちる |
| 2 余分な項目が公開される | 直った。`clean` は文字列を `home` と `cube.at` しか通さず、どちらも `valid` が決まった値に限っている。今の `samples/collected-*.truth.json` 17 個では、`clean(t)` は image と note を除いた元と同じだった（落ちる項目は無い） |
| 3 読めない写真で取り込みが止まる | **一部だけ直った**。下の新 1 |
| 4 マージのあとの `push --delete` | 直った（消した） |
| 5 開いた PR があると、同じ組の PR がもう 1 つできる | 直った（`gh pr list` で、開いている `claude/collected-import-*` があれば何もしない）。テストは無い（下の新 4） |
| 6 マージの前に main を取り込んでいない | 直った。偽の `gh` で、main が動かない・1 回動く・動いたあとの checks が落ちる、の 3 通りを試した。それぞれ、A でマージ（checks 1 回）、B でマージ（checks 2 回）、開いたまま残す、になった |
| 7 再起動で worktree が残る | 直った。同じ作りの試しのスクリプトに SIGTERM を送ると、`finally` が動き、`subprocess.run` の子プロセスは消え、一時ディレクトリも消えた。残る点は下の新 2 |
| 8 `gh pr create` の失敗を見ていない | 直った（リモートのブランチを消して記録する） |
| 9 末尾が同じ id の上書き | 直った（`ids` と `i`）。テストでは確かめられていない（下の新 3） |
| 10 文書 | 直った。README.md・index.html・docs/raspi.md・recognizer/README.md・analyzer/README.md・HANDOVER.md・CREDITS.md の該当箇所を読んだ。`APP_VERSION` と `__version__` は 0.67.0 で揃っていて、0.66.0 は残っていない |
| 11 CLAUDE.md の決まりが 2 つ並ぶ | 直った（「手で入れるときは」とし、自動の分は別の項目に分けた） |
| 12 テストの判定が重なっている | 一部だけ直った（下の新 3） |
| 13 mermaid に「いいえ」が無い | 直った |

## 要修正

### 新 1. `recognizer/import_collected.py:47`・`:129` 認識が例外で止まる組が 1 つあると、取り込みが止まる（前の 3 の残り）
- 何が起きるか: `pick` が除くのは、画像として読めない写真だけ。truth が `valid` を通っても `evaluate.run` が例外になる組（`misreads` が `["読めなかった"]` を返す組）は選ばれ、`add` までは進む。ところが `check_accuracy.py --update` の `measure` は例外を拾わないので（`check_accuracy.py:32-50`）、`subprocess.run(..., check=True)` が `CalledProcessError` になる。読み違いのある組は `collected/` から消えず、古い順の 10 組に入ったままなので、次の測り直しでも同じ組を選んで同じところで落ちる。結果として、それ以後の取り込みは止まったまま（`import.log` には毎回 `failed: CalledProcessError(...)` が残る）。
- 実測: 四隅を次のようにした screen1 で、`collected.valid` は True、`misreads` は `['読めなかった']` を返し、`add` は通った。そのあと `check_accuracy.measure` は次の例外を出した。
  - 4 つとも同じ点 `[[100,100]]*4`: `TypeError('iteration over a 0-d array')`
  - 4 つが一直線: `ZeroDivisionError('float division by zero')`
  - 1 つが NaN: `ValueError('cannot convert float NaN to integer')`
  - 1 つが inf: 同じ `ValueError`
  - 1 つが 1e300: `TypeError`
  - 写真の外まで広げた四隅は例外にならなかった
- ついでに分かったこと: NaN や inf の四隅は、`json.dumps` が `NaN`・`Infinity` と書くので、JSON の規格に合わないファイルが `samples/` に入る。塗りも崩れ、元のまま残る画素は、正しい四隅なら 43% のところが 54% になった（盤の外の一部が塗られずに残る）。
- 送れるのは開発機の LAN の端末だけ。PWA から同じ点や一直線の四隅を送れるかは未確認。

## 検討

### 新 2. `recognizer/import_collected.py:117` SIGTERM で止まったことが `import.log` に残らず、残った PR がそのあとの取り込みを止める
- 何が起きるか: `sys.exit(1)` は `SystemExit` を投げるが、`run` が捕まえるのは `except Exception` だけなので、`failed: ...` も書かれない（試しのスクリプトで確かめた）。PR を作ったあとに止まると、その PR は開いたまま残り、そのあとの取り込みは「nothing added while … is open」で止まる。docstring（`:9-10`）と docs/raspi.md は、開いたまま残るのを「checks が落ちたとき・main とぶつかったとき」としていて、再起動で残ることは書いていない。開発機の `post-merge` は、main を pull するたびにサービスを再起動する。
- 再起動が checks の待ちと重なる頻度は未確認。

### 新 3. `analyzer/test_collected.py:85-125` 末尾が同じ id・空の id・同じ名前の判定を、それぞれ外しても落ちない
- 1 か所ずつ壊して `uv run pytest analyzer/test_collected.py` を実行した（壊す前は 6 件とも通る）:

  | 壊したところ（`import_collected.py`） | 結果 |
  |---|---|
  | `i and`（空の id）を消す | **通る** |
  | `i not in ids` を消す | **通る** |
  | `not added(n)` を消す | **通る**（下の「作り込みすぎ」のとおり、外しても挙動は変わらない） |
  | `seen \|= …` を消す | 落ちる |
  | `h not in seen` を消す | 落ちる |
  | `seen.add(h)` を消す | 落ちる |
  | 読めるかどうかの確認（`cv2.imread`）を消す | 落ちる |
  | 古い順の並べ替えを消す | 落ちる |
  | `clean(t)` の代わりに `t` を書く | 落ちる |
  | `cube` をそのまま写す | 落ちる |
  | `read` の項目を絞らない（型だけで絞る） | **通る**（int の余分な項目が残るだけで、文字は入らない） |
  | `dice` を書かない | **通る** |
  | 塗らない | 落ちる |
  | `collected.py` の `BG_IMPORT` の条件を外す | 落ちる |
  | `to_samples` に全部の組を渡す | 落ちる |
  | `merge()` の `if head() == sha:` を `if True:` にする | **通る** |

- `i not in ids` が効かない理由: `other()` は、どの写真でも同じ画素を反転させる。だから `user-5-x-ccc` と `user-3-ccc` は同じ写真になり、sha で除かれてしまう（テストのコメントは「another pair that would be collected-ccc too」）。
- `dice` が効かない理由: `clean` が今の項目を落としても、どのテストも気づかない。今の 17 個では落ちていないが（上の表の 2）、項目を落とすと、基準を書き直すときに何も言われないまま採点が変わる。

### 新 4. `recognizer/import_collected.py:109-165` `_run` と `merge` にテストが無い
- 開いた PR があれば止まる（`:115`）、`gh pr create` が失敗したらリモートのブランチを消す（`:140-142`）、main が動いたら checks を待ち直す（`:162`）は、どれもテストで確かめていない。`merge` は偽の `gh` を渡せばそのまま試せる（上の 6 はそのやり方で確かめた）。

### 新 5. `recognizer/import_collected.py:156-158`・`:160` checks がまだ出ていないときと、`update-branch` の扱い（未確認）
- 30 秒待っても checks が出ていないと、`gh pr checks` が 0 でない値を返して「checks failed」になりうる。今は、そうなるとそのあとの取り込みがすべて止まるので（上の 5 の直し）、前より影響が大きい。
- `gh pr update-branch` について、次の 2 つは確かめていない（実際の PR では試していない。gh 2.102.0 の help には書いていない）。
  - 既に main が入っているとき、0 を返すか
  - main を取り込み終えてから戻るか。戻る前に `head()` を読むと古い sha のまま抜け、`--match-head-commit` で「not merged, left open」になる。止まりはするが安全な側に倒れる

## 作り込みすぎ

- `recognizer/import_collected.py:47`: delete: `not added(n)`。`n` 自身が `d` にある以上、`added(n)` が真なら、`:43` の `seen |=` が `n` の写真の sha を必ず入れるので、`h not in seen` で既に除かれる（上の表で、外しても落ちなかったのはそのため）。消すかどうかは好みの範囲（「同じ名前」を読み手に見せる意味はある）。

net: -1 lines possible.

## 問題の無かった観点

- `merge()` の流れ（checks → `update-branch` → head が変われば待ち直す → `--match-head-commit`）: 偽の `gh` の 3 通りで、意図どおりに動いた。
- `clean()`: 通る文字列は決まった値だけ。今のサンプルの項目は落とさない。
- SIGTERM: `finally` で worktree とブランチを消す。`subprocess.run` の子プロセスは消える。
- 作業中のチェックアウト: `gh` を `cwd=REPO` で使うが、`--head` を指定していて、チェックアウトは切り替えない。
- バージョン: analyzer 0.67.0（`index.html` の文言を変えたため）、`APP_VERSION` も同じ。recognizer は道具だけの変更なので上げない（CLAUDE.md どおり）。
- 範囲: 指示に無い変更は無い。
