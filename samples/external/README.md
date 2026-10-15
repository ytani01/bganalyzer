# 外部の画像（画像はリポジトリに入れない）

著作物なのでリポジトリに入れられない画像の出典 URL と、目で読んだ正解です。
今あるのは、USBGF の [Bray's Learning Curve](https://usbgf.org/learn/increase-your-skill/brays-learning-curve/) の盤面図（`bray-*`）と、
Backgammon Galaxy の記事の写真（`galaxy-*`、下の節）です。
`*.truth.json` の `url` から `recognizer/evaluate.py` が画像を取ってきて、このフォルダに保存します（`.gitignore` 済み）。

```bash
cd recognizer && uv run python evaluate.py ../samples/external/*.truth.json
```

正解の色の呼び方は他のサンプルと同じで、`bray-*` では手前（図の下側、赤い駒）が white、奥（白い駒）が black。
図の右上と右下の「10/17」などはマッチのスコアで、上がった駒の数は 15 − 盤上の数です。ピップ数は図の表示と一致しています。

## Backgammon Galaxy のダブルの説明（PI-032）

[How to Use the Backgammon Doubling Cube](https://www.backgammongalaxy.com/how-to-use-the-backgammon-doubling-cube) に載っている、
実物の盤を撮った動画のコマです。`galaxy-cube2-near` は手前の左のトレイにキューブ 2（手前の側が持っている）。
盤の右の端が画像から少し切れているので、右の 2 隅は画像の外を指しています。ケースの左右が同じ平面に無く、四隅で両方を合わせきれないので、
主にキューブの数字を読むときの答えとして使います。同じページのキューブ 4 を奥に置いたコマは、盤の手前が切れていて駒が数えられないので入れていません。
