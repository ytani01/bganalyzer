# TODO-125 verifier 報告

実行: Playwright（390x844、1300 は幅だけ変更）、別起動のサーバー（8001、終了済み）、screen1 を読ませ、`BgApp.update` で board と fromPhoto を差し替えて `#count-mark` を読んだ（駒の足し引きはクリックでなく state 差し替え。表示側のコードは同じ `part` を通る）。スクリプト: scratchpad の v.py。

- 版: ヘッダー `a0.69.2 · r0.24.0 · 23d510f`、`/version` analyzer 0.69.2、app.js `APP_VERSION` 0.69.2。一致
- 色（写真から読んだ盤）: 白 16 個 `many` `⚠ 白 16/15` rgb(198, 40, 40)、黒 14 個 `few` `・黒 14/15` rgb(201, 154, 0)。一致
- 色（逆）: 白 3 個 `few` rgb(201, 154, 0)、黒 16 個 `many` rgb(198, 40, 40)。白黒で別々。一致
- 位置（390、写真なし）: `#count-mark` top 96.8 / 盤面図 `.board-wrap` top 121.8。盤のすぐ上。一致
- 位置（390、元の写真を並べる）: 写真 152.8 / count-mark 446.4 / 盤 471.4（1 列、写真と盤の間）。一致
- 位置（1300、元の写真を並べる）: 写真 top 190.3 / count-mark 190.3 / 盤 215.3、count-mark の left 654 = 盤の left 654（2 列、盤の列の上）。一致
- 「盤に駒がありません」（全部空、手作り）: `few` rgb(201, 154, 0)。一致
- 手で作った盤（fromPhoto=false）で白 3・黒 3: 非表示（hidden=true）。一致。同じ盤で fromPhoto=true なら両方 `few` で出る
- 変更ファイル（main との差）: TODO.md, analyzer/app.py, analyzer/static/app.js, analyzer/static/index.html, analyzer/static/style.css。ほか未追跡は archives/agents/TODO-125/ のみ。範囲は想定内（指示文に変更ファイルの指定は無かったので、TODO-125 の範囲かの照合はしていない）
- 確かめていない: 実クリックでの駒の足し引き、テスト全体・全サンプル（CI の担当）、変更前に戻した比較
- 判断が要る点: なし
