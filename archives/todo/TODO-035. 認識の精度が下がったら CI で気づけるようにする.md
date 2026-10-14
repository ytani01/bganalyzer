# TODO-035. 認識の精度が下がったら CI で気づけるようにする

- **担当:** 引き継ぎ先（2026-10-14 着手）
- [x] `recognizer/evaluate.py` の結果が今の正解数より下がったら、GitHub Actions を失敗させる（`recognizer/check_accuracy.py` と `accuracy_baseline.json`、`.github/workflows/accuracy.yml`）

今の CI（`.github/workflows/test.yml`）は `uv run pytest analyzer` だけで、写真の認識は測っていない。
`docker.yml` も screen1 を1枚通して解析まで動くかを見るだけで、正解かどうかは見ない。
認識を変えて精度が下がっても CI は緑のままで、`evaluate.py` を手で走らせないと気づけない。

案: サンプルごとの今の正解数（ポイント・バー・ダイスなど）をファイルに置き、`evaluate.py` の結果が
それを下回ったら失敗する。上がったときはファイルを更新する（`recognizer/README.md` の「精度」の表と揃える）。

- 全 23 枚の `evaluate.py` は、2026-10-14 にクラウドで約 130 秒。CI に入れられる長さ
- x86_64 と Raspberry Pi で結果が違うことがある（TODO-028 の四隅など）。CI は x86_64 なので、基準は x86_64 で測る
- `--app`（PWA と同じように縮めて送る）も測るかは、着手するときに決める

## やったこと（2026-10-14 に完了: PR #99）

- `recognizer/check_accuracy.py` が `samples/*.truth.json` の全部を読み、サンプルごとのポイント・バー・ホーム・ダイス・キューブを
  `recognizer/accuracy_baseline.json` と比べる。`--update` で基準を書き直す
- GitHub Actions の `accuracy`（`.github/workflows/accuracy.yml`）が、recognizer・samples・依存を変える PR と main への push で走る（約 70 秒）。
  結果は注釈（notice）にも出すので、ログを開けない環境でも API や PR の画面から読める
- `--app` は CI では測らない（ブラウザとの画素の差で結果が動くため）
- わかったこと: GitHub の実行機は回ごとに CPU が違い、OpenCV・NumPy・OpenBLAS が CPU ごとに命令（AVX-512 など）を選ぶため、
  そのままでは 1〜4 ポイント動くサンプルがあった（AMD EPYC 9V45 で 495 → 490）。`check_accuracy.py` の中だけ AVX2 までに揃えると、
  クラウドと GitHub の 4 種類の CPU（7 回）で全部同じ 495 になった。まだ試していない CPU のために 1 枚ごとの 1 ポイントの低下は許し、合計は厳密に見る。
  `cv2.setUseOptimized(False)` で揃える案は、5 枚の結果が 1〜4 ポイント変わりアプリと違う動きを測ることになるので採らなかった
