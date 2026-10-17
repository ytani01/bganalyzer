# 確認報告（TODO-115 / TODO-109 / TODO-117）

対象: claude/todo-109-115-117、コミット f31c78c。サーバーは 127.0.0.1:8011 で起動（確認後に停止、8011 は応答なし）。
スクリプト: archives/agents/TODO-115/check.py（CDP で live_view のブラウザに接続、新しいページで操作。終了コード 0、console error なし）。

## 結果（項目ごと）

- 117.1 `#history .note` の textContent: 「最近の 100 枚を、この端末の中だけに残します。」一致。#history は hidden のまま。`rg -n "最近の 10 枚" analyzer` は 0 件（終了コード 1）。
- 109.2 `details.tips li` は 5 行。「手前の人が写真の下になる向きで撮る（バーが縦になるように）。向きが違うときは、四隅の画面で 90° 回せる」「ダイスは、見やすい位置に置く」「カップなど、不要なものはボードの外に置く」の 3 行を含む。「ダイスやカップは盤の外に置く」は無い。
- 115a `#hdr-version`: 「a0.65.0 · r0.23.2 · f31c78c」。a0.65.0 で始まる。`/version` も analyzer 0.65.0、commit f31c78c。
- 115b 写真の画面: `#auto-speak-opt` は hidden。盤面の画面（手で入力後）: 見える。`#auto-speak` は既定でオフ（checked=false、localStorage autoSpeak は未設定）。
- 115c オフのまま解析 → 結果の画面、2 秒後の `#speak` aria-pressed = "false"。
- 115d 盤面でオンにして解析 → `#speak` aria-pressed が "true"（待ち時間 0.0 秒で確認。音は未確認）。localStorage autoSpeak = "on"。
- 115e 結果から `#back` で盤面へ → `#speak` aria-pressed = "false"。
- 115f 再読み込み → 盤面で `#auto-speak` が checked、localStorage autoSpeak = "on"。最後にオフへ戻し、localStorage = "off"、checked = false。
- ブラウザのコンソール error / pageerror: 0 件。

## 合わないもの

なし。

## 確かめられなかったこと・判断が要る点

- 読み上げの音は聞いていない。aria-pressed が "true" になったことで「読み上げが始まった」と見ている（指示どおり。音声の有無は未確認）。
- 115d の aria-pressed "true" は、読み上げが終わると戻るかどうかを見ていない（指示になかった）。
- 変更ファイルの範囲の確認はしていない（指示に含まれず）。HEAD~2..HEAD の変更は TODO.md、analyzer/README.md、analyzer/app.py、analyzer/static/app.js、analyzer/static/index.html の 5 ファイル。作業ツリーに未コミットの変更は無い（`archives/agents/TODO-115/` だけが未追跡）。
- 判断が要る点: なし。
