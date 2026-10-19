# TODO-149 verifier 報告

方法: 作業ツリーで uvicorn を 127.0.0.1:8011 に起動、/usr/bin/chromium（headless、390x844）を Playwright で操作。各項目 1 回。
スクリプト: archives/agents/TODO-149/verify_to_start.py（写真は samples/collected-app-green-far.jpg）。サーバーは停止済み（8000 は触っていない）。

- 1 一致: 写真の選択 title='写真の選択'、#to-start 見えない
- 2 一致: 四隅 title='四隅の調整'、見えない
- 3 一致: 写真から進んだ盤面 title='盤面の確認/修正'、見える
- 4 一致: 手で入力した盤面 title='盤面の確認/修正'、見えない
- 5 一致: 結果 title='解析結果'、見える
- 6 一致: 結果から「‹ 戻る」で手入力の盤面に戻ると title='盤面の確認/修正'、見えない

食い違いなし。判断が要る点なし。変更ファイルは確認していない（依頼範囲外）。
