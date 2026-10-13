# TODO-017 verifier 報告

結論: 正解・出典・大きさ・evaluate の値は一致。食い違いは README の 1 か所のみ（下の「食い違い」）。

## 一致したもの
- case-dice の points 24 個: 写真と一致（白 5@6、2@8、5@13、2@24。黒 2@1（右端の影の中に 2 個見える、明るくして確認）、5@12、2@17、5@19）。dice [5,3] も一致（赤 3・白 5）。白 14・黒 14
- nardy-midgame の points 24 個: 一致（白 15、黒 15）。dice null 妥当
- rollup-oblique の points 24 個: 一致（初期配置、黒 17 に 3 個）。dice null 妥当（ダイス 4 個＋キューブ）
- 四隅（truth を元の写真に重ね描き）: 3 枚とも遊戯面をおおむね囲む。rollup は奥の辺が奥の列の駒（19〜24 付近）の上端を少し切る程度
- 顔・個人情報: 3 枚とも無し（rollup は背景が大きくぼけた人影らしきもののみで識別不可。拡大して確認）
- CREDITS.md 3 行: Commons API の作者・ライセンス・タイトルと一致（Martina Grosty CC BY 2.0 / StatisksExpert CC BY-SA 4.0 / Ilker Bicakci CC BY-SA 4.0）。URL は題名と一致
- 大きさ: 3 枚とも 1920x1440。元は 2432x1824・2560x1920・4032x3024（いずれも 4:3）で長辺 1920px 版と一致
- evaluate.py（終了コード 0）: case-dice 18/24、nardy-midgame 18/24、rollup-oblique 13/24。README の 18・18・13 と一致
- README の説明: case-dice（1/5/6/19/20/24 が外れ、右側のずれと整合）、nardy（外れは 3,9,15,17,19 の黒 5 か所と 4 の白 1 個）と一致。四隅の誤差・「見つからない」の記述は未検証（下記）

## 食い違い
- recognizer/README.md の rollup-oblique の行「空いた三角形 10 か所に駒があると読み」: evaluate の出力では、正解が 0 で認識が非 0 のポイントは 2,4,10,14,16,18,20,21,23 の **9 か所**。ほかに外れたのは 19（-5 を -3）と 24（+2 を 0）で、計 11 か所。10 ではない

## 確かめなかった・判断できないこと
- README の四隅の誤差（nardy 2.4%、case-dice・rollup が「見つからない」）は走らせていない（依頼の範囲外）
- case-dice の黒 2 個は影の中でほぼ黒く、明るさを上げて見える範囲での判断
- Raspberry Pi 以外（x86_64）での値は測れない
