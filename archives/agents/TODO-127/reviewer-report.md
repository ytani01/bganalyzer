# TODO-127 reviewer の報告

対象: `git diff main`（未コミット。`tools/live_view.py`・`CLAUDE.md`・`docs/raspi.md`・`TODO.md`）。
Playwright の挙動は、uv のキャッシュにある playwright 1.62.0 の `_impl/` を読んで確かめた（動かしてはいない）。

## 要修正

なし。

## 検討

### 1. `tools/live_view.py:43-46` 写真と `.truth.json` の片方だけ名前が変わると、組がずれる（実害は未確認）

- 何が: `exportSample()`（`analyzer/static/app.js:1051-1055`）の名前は `BgSample.baseName()`（`analyzer/static/sample.js:10-13`）で、
  **分までしか入っていない**（`user-YYYYMMDD-HHMM`）。同じ分に 2 回書き出すと、2 回目は
  `user-…-HHMM (1).jpg` と `user-…-HHMM.truth (1).json` になる。ところが `.truth.json` の中の `image` は
  `user-…-HHMM.jpg` のままなので、**2 回目の正解が 1 回目の写真を指す**。
  前の書き出しの片方だけ消してあった場合も、片方だけ `(1)` が付いてずれる。
- なぜ: 上書きしないという要件（TODO.md）は満たしているが、2 つで 1 組のファイルなので、
  `samples/` に入れるときに名前で組を作ると取り違える。Chromium が自分で保存するときの名前の付け方も同じなので、
  この差分が新しく作った問題ではなく、アプリの名前が分単位なことから来ている。
- 境界線上の判断なので報告だけ。

### 2. `tools/live_view.py:46` と `:69` 保存に失敗すると、live_view が黙って終わる（実害は未確認）

- 何が: sync API ではイベントハンドラーの例外は `Connection._on_event_listener_error` が標準エラーに出して `_error` に取っておき、
  **次の API 呼び出しで投げ直す**（`_connection.py:138-141`, `:567-571`）。次の呼び出しは `page.wait_for_timeout()` で、
  `save_as` が投げるのは Playwright の `Error`（ダウンロードの取り消し・失敗など）なので、`main()` の
  `except Error:   # the window was closed` に入り、**窓を閉じたのと同じに扱われて終わる**（ブラウザも閉じる）。
  `OSError`（`~/Downloads` に書けない等）ならトレースバックで落ちる。
- なぜ: 1 つのダウンロードの失敗で、開いておく窓そのものが消える。blob URL のダウンロードが失敗する場面は
  ほぼ無いので、起きる頻度は低い。また、`save_as` で待っていた greenlet が再開したあとに出た例外が、
  本当に上の経路を通るか（初回の `g.switch` の try の外になる）は読み切れていない。未確認。

### 3. `tools/live_view.py:42-46` 同じ名前のダウンロードが同時に来ると上書きする（実害は未確認）

- 何が: 各ハンドラーは別の greenlet で動き（`_connection.py:549-556`）、`save_as` で待つ間に次のハンドラーが走る。
  `path.exists()` を見てから `save_as` が書き終えるまでの間に同じ名前が来ると、どちらも同じ `path` を選ぶ。
- なぜ: 「ファイルに書き出す」の 1 回分は写真と `.truth.json` で名前が違うので起きない。
  同じ分に 2 回素早く押したときだけ。報告だけ。

## 問題の無かった観点

- `context.on("page")` は `context.new_page()` の page にも付く: `BrowserContext._pages` に足すのは `_on_page`（page イベント）だけで（`_browser_context.py:240-242`）、`new_page` はその page を返すので、ハンドラーは付く。ハンドラーは `new_page` の前に登録してあり、取りこぼさない。新しいタブ（popup）にも付く。
- ハンドラーの中で `save_as` を呼んでよい: sync API はイベントごとに `EventGreenlet` を作って動かすので、中で待つ呼び出しをしてよい（`_connection.py:549-556` のコメントどおり）。
- 1 回の操作で 2 つ続くダウンロード: イベントごとに別の greenlet で、1 つ目が `save_as` で待つ間に 2 つ目も受ける。取りこぼさない。イベントは `page.wait_for_timeout()` の間に配られる。
- 名前の重複回避: `.truth.json` は `name.truth (1).json` になり、docs/raspi.md の「`名前 (1).拡張子` のように」と合う（Chromium と同じ付け方）。
- 文書と実装: CLAUDE.md・docs/raspi.md・docstring の保存先は実装と合っている。`rg live_view` でほかに古い説明は無い（archives は対象外）。
- 範囲: analyzer・recognizer は変えておらず、版を上げないのは CLAUDE.md の「バージョン」どおり。指示に無い変更は無い。
- コメント: docstring の追記は「なぜ」（窓の一時フォルダではなく）を書いている。
- テスト: 道具の変更で、確かめは verifier の実測で行う予定。テストを足す必要は無い。
- 作り込みすぎ: なし。
