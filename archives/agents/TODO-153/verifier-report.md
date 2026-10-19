# TODO-153 確認（ローカルホスト、live_view の Chromium に CDP でつないで操作）

準備: トップの作業ツリーで git pull、post-merge で再起動。/version = analyzer 0.86.0 / recognizer 0.28.0 / commit 66e1674。
条件: 5 ポイントマッチ、白 4・黒 0（クロフォードできる）。各項目 1 回。スクリプト: scratchpad の chk.py（tools/pi_ui_check.py の open_app/read_photo を使用）。

- 1 合った: キューブ black・クロフォード false → クロフォードを入れる → キューブ centre・クロフォード true。alert なし。
- 2 合った: クロフォード true・キューブ centre → キューブを white にする → クロフォード false・チェックも外れる。alert なし。
  ヘッダー（盤の画面）は前「5 ポイントマッチ（クロフォード）」→後「5 ポイントマッチ」。
- 3 合った: クロフォード true・キューブ centre のまま screen-app-green-far（truth の cube は black、value 2）を読み取り。
  読み取り後: キューブ black・クロフォード false（チェックも外れた）・ヘッダー「5 ポイントマッチ」・alert なし・result は未解析（null）。
  「解析する」で解析できた（最善手 bar/20、alert なし）。

食い違い: なし。
注意（実害は未確認）: 1・2 は盤の画面を出さずにシートの部品を DOM 経由で操作した（seg ボタンの click、チェックボックスと select の change イベント）。実際の指での操作ではない。
