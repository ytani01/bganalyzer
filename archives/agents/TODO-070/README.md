# TODO-070 の測定と判断

## 分担

- main: 実装と、実装前の測定（`measure_cropped.py`）・手元の Playwright（`check_pwa.py`）。PWA の 1 画面に閉じた変更なので、実装の担当は分けなかった
- reviewer（Opus 5.5 / high）: 状態の引き継ぎや他の操作との競合など、分岐が変わるので入れた。`reviewer-report.md`
- verifier（Sonnet 5.5 / medium）: reviewer の指摘を直したあとに、Playwright で操作を確かめた。`verifier-report.md`・`verify_extra.py`

## 切り抜いた画像で四隅を探すとき、`crop` に画像全体を送るか

`measure_cropped.py`（`MARGIN` は盤の外接矩形に足す余白。盤の辺に対する割合）。56 枚、誤差は切り抜いた画像の長辺に対する割合。

| 余白 | crop なし（3.6% 以内 / 外れ / 見つからない） | crop = 画像全体 |
|---|---|---|
| 0.15 | 24 / 32 / 0 | 25 / 28 / 3 |
| 0.5 | 36 / 20 / 0 | 37 / 16 / 3 |
| 1.0 | 36 / 19 / 1 | 35 / 14 / 7 |

screen2（余白 0.15）は crop なし 48.8% → 画像全体 3.4%。ゆるく切り抜くと 3.6% 以内が 1 件減るが、
外れの多くが「見つからない」（四隅は長方形のまま）に変わるだけなので、切り抜いた画像は画像全体を `crop` で送る。

## reviewer の指摘への対応

- 原寸のまま回すと端末の canvas の上限を超えうる → 編集後の画像の長辺を `UPLOAD_MAX`（2048）までにした（送る画像・履歴の写しもこの大きさまでなので失うものは無い）。`toBlob` の null は reject する
- 編集中に盤面の画面へ行くと `edit` が残る → 画面が変わるとき `edit: null`
- 走っている四隅探しと `PhotoHistory.replace` の競合 → 確定の始めに `search++`
- 90° の矩形の変換のテスト → app.js のハンドラーの中なので単体のテストは足さず、verifier の Playwright で確かめる
