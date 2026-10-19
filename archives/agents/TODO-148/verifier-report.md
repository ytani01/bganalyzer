# TODO-148 verifier 報告

方法: 作業ツリーで uvicorn を 127.0.0.1:8011 に起動、/usr/bin/chromium（headless、390x844。live_view は動いていなかった）を Playwright で操作。
スクリプト: archives/agents/TODO-148/verify_to_start.py。各項目 1 回。about:blank を開いてからアプリへ移動。写真は samples/collected-app-green-far.jpg。サーバーは停止済み（8000 は触っていない）。

- a 一致: 写真の選択の画面 title='写真の選択'、#to-start は見えない
- b 一致: 四隅 title='四隅の調整'、#to-start 見える。#back x=16 w=67.8、#to-start x=91.8（戻るの右）。押すと title='写真の選択'・非表示。go_back で url=about:blank（アプリを出た）
- c 一致: 盤面 title='盤面の確認/修正'、見える。押すと title='写真の選択'。go_back で url=about:blank
- d 一致: 結果 title='解析結果'、見える。押すと title='写真の選択'。go_back で url=about:blank

食い違いなし。実害は未確認の点もなし。変更ファイルは確認していない（依頼範囲外）。archives/agents/TODO-148/ にスクリプトと本報告を追加した。
