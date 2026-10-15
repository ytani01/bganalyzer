# verifier 報告（TODO-030、コミット 3373b96）

## 問題あり（1 件）
- **samples/collected-sj1vrx.jpg に個人名とメールアドレスが写っている。**
  右側の紙（Problem 9/10）の下端、表示 2000x1502 で約 (1640-1750, 1160-1190)、元画像では約 (1670-1785, 1180-1215)。
  文字は "Ichikawa Masanori" と "itikawa@itikawa.com"。目で読めた。
  顔は無い。この名前が公開してよいものか（クイズ作者の公開情報かもしれない）は、判断できない。
  公開してよいか利用者に確認するか、塗りつぶすかの判断が要る。

## 気になる点（境界線上。実害は未確認）
- collected-o32w4i.jpg（アプリ画面）: "Game ID: 647953726"、残高 $418、国旗の小さな絵、左上に切れた丸いアイコン。ユーザー名は読めない。
- collected-l9azfe.jpg: 紙の "Wydliffe Brothers" とロゴ（会社名、人物の写真に見えるロゴ）。個人名ではない。
- collected-a8qvq6.jpg: 左下の紙に日本語の文字（回転していて読めない）。手と腕・袖は写るが顔は無い。
- collected-3wo2ot.jpg: 胴体と腕（首から上は写っていない）、スマホ、カードの文字は読めない。tad9pt: 左端に服の一部のみ。

## 顔・名前・アカウント名なし（1 行ずつ）
2aunci（Las Vegas Open の盤画面。名前なし）/ 4b88u3 / 5wxq9t / bfqwve（XG の画面。名前なし）/ er0y2w（指先のみ）/ h8ilqt / s5dd7x / si3vsd / tad9pt / w8eaks（アプリ画面。名前なし）: 顔・名前・アカウント名は見えない。

## 2. truth.json
15 件すべて JSON として読め、`image` は実在。白・黒とも points の正負 + bar + off で 15（キーは bar_white/bar_black/off_white/off_black）。

## 3. 精度
`R=... python recognizer/check_accuracy.py` 終了コード 0（末尾 `points: 885/984 (baseline 885)`）。`--update` は付けていない。

## 確かめなかったこと
画像の拡大はしていない（Read の縮小表示で見た。小さな文字は見落としうる）。ファイルの EXIF は見ていない（rg/exiftool 未実施）。
