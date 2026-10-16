# TODO-070. 写真そのものを矩形にトリミングし、回転できるようにする

| | main | 担当 |
|---|---|---|
| 見込み | Opus 5.5 / effort high | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Sonnet 5.5 / medium） |
| 実施 | Opus 5.5 / effort high | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Sonnet 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | high | 86 | 42,141 | 142,740 | 5,944,912 | 77% |
| reviewer | Opus 5.5 | high | 46 | 3,923 | 86,000 | 1,330,472 | 18% |
| verifier | Sonnet 5.5 | medium | 24 | 384 | 46,871 | 381,531 | 5% |
| 合計 |  |  | 156 | 46,448 | 275,611 | 7,656,915 | 計 7,979,130 |

- verifier は定義のモデルが haiku。Playwright で 5 つの操作を確かめ、数値を突き合わせるので、見込みどおり Sonnet 5.5 に上書きした
- reviewer・verifier の effort は、見込みの行に書いた値を Agent ツールでも渡した（定義の値と同じ）
- 集計は決着のコミットの前（現在時刻まで）

## きっかけ

ユーザーの依頼（2026-10-16）: 四隅を指定するのとは別に、画像本体を矩形にトリミングし、回転もできるようにする。

決めたこと（2026-10-16 ユーザー）:
- 回転は「左に 90°」「右に 90°」のボタンと、±45° までの細かい角度（スライダー）
- 四隅の画面に「画像を編集」を置き、押すと編集の表示に切り替える。確定すると、編集後の画像で四隅を探し直す
- 今の「範囲を囲む」「範囲を戻す」（TODO-068）は消し、画像のトリミングにまとめる

## やったこと

analyzer 0.45.0（`sw.js` の `CACHE` は v53）。recognizer は変えていない。

- `analyzer/static/photo.js` に `turn(image, deg, rect, maxSide)`: 時計回りに回した外接矩形（余りは黒）を、分数の矩形で切り抜いた canvas
- `analyzer/static/app.js`: `state.edit`（`turn`・`angle`・`rect`）。編集中は 1280 px に縮めた写しを回して見せ、ドラッグで矩形を描く（90° 回すと矩形も一緒に回す）。
  「確定」で原寸の写真から作り（長辺は `UPLOAD_MAX` の 2048 まで）、`startPhoto` に渡す。読み取った盤面と設定は残し、四隅は探し直す。
  切り抜いた写真は `photo.trimmed`（履歴にも残す）で、そのときは `/find-corners` に画像全体を `crop` で送る。画面が変わると編集はやめる
- `analyzer/static/history.js` に `replace`: 履歴の写真と縮小画像を編集後のものに替える（「Pi に残す」・書き出しもこの写しを使う）
- `analyzer/static/corners-view.js`: 表示の拡大（`crop`）を消し、描いた矩形を外側を暗くして出し続ける
- `index.html`: 「範囲を囲む」「範囲を戻す」を消し、「画像を編集」と編集の操作（`#edit-tools`）を足した
- `/find-corners` の `crop` は残した。切り抜いた画像は、画像全体を `crop` で送ると盤が画像の大部分を占めてよいものとして探すので、
  screen2 が 48.8% → 3.4% になる。ゆるく切り抜いても悪くなるのは「見つからない」が増える程度（`archives/agents/TODO-070/README.md`）
- analyzer/README.md の四隅の画面と `/find-corners` の説明、docs/PI_CHECKS.md の PI-047 のスマホの確認を新しい画面に合わせた

## 確かめたこと

`archives/agents/TODO-070/verifier-report.md`。`uv run pytest analyzer` 84 passed。390x844 の Playwright（`check_pwa.py`・`verify_extra.py`）で:

- collected-sj1vrx を盤のまわりで切り抜いて確定 → 四隅が見つかり、正解とのずれ 21.8 px（TODO-068 の囲む方法は 22.3 px）。履歴の画像も 428x382 に替わった
- photo2 を左に 90° 回した写真で「右に 90°」→ 確定 → ずれ 150.9 px（4624 px の写真で 3.3%。元の向きの `check_corners.py --app` と同じ）
- 矩形を描いてから 90° 回すと、確定後の画像の幅と高さが入れ替わる（819x615 → 615x819）。10° 回すと黒い隅のある外接矩形で長辺 2048
- 「やめる」で何も変わらない。編集中に写真の画面へ戻って開き直すと四隅の表示。切り抜いた写真だけ「もう一度検出」で `crop` が入る

## 残ること

- スマホでの確認（docs/PI_CHECKS.md の PI-047、ユーザー）

## 分担の振り返り

- **reviewer** は、TODO.md で TODO-069 の「版を上げる」にチェックを入れていたこと、原寸のまま回すと iOS の canvas の上限を超えうること
  （以前は 2048 に縮めてから描いていた）、`toBlob` の null、編集中に盤面の画面へ行くと `edit` が残ること、走っている四隅探しと履歴の書き換えの競合、
  ゆるく切り抜いたときの `crop` の根拠が無いことを見つけた。どれも main の手元の確認（Playwright）では出ないもので、レビューを入れた意味があった。
  **verifier** は食い違いを見つけなかった。`post_data` が空で FormData を包んで値を拾ったので、送った body そのものは見ていない
- 見込みとの食い違いは無い。main が実装前に Playwright の確認スクリプトを作って流したので、verifier は同じスクリプトと追加 5 項目で済んだ
- 次に同じ規模（PWA の 1 画面に操作を足す）なら同じ組み方でよい。トークンの 77% は main で、その大半は会話の長さによる cache_read。
  実装前に app.js 全体（1,000 行）を読んだ分は削れない。reviewer には「端末の制限（canvas・メモリ）」を見る観点を依頼文に最初から入れる
