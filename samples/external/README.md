# 外部の盤面図（画像はリポジトリに入れない）

USBGF の [Bray's Learning Curve](https://usbgf.org/learn/increase-your-skill/brays-learning-curve/) に載っている
盤面図の出典 URL と、目で読んだ正解です。図は著作物なのでリポジトリには入れていません。
`*.truth.json` の `url` から `recognizer/evaluate.py` が画像を取ってきて、このフォルダに保存します（`.gitignore` 済み）。

```bash
cd recognizer && uv run python evaluate.py ../samples/external/*.truth.json
```

正解の色の呼び方は他のサンプルと同じで、手前（図の下側、赤い駒）が white、奥（白い駒）が black。
図の右上と右下の「10/17」などはマッチのスコアで、上がった駒の数は 15 − 盤上の数です。ピップ数は図の表示と一致しています。
