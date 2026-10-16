# TODO-066 verifier 報告

スクリプト: `archives/agents/TODO-066/verify.py`（サーバーは 8765 で起動し、PID 408216/408221 を kill 済み）。スクリーンショット: `outcome.png`。コードは変えていない。

## 1. API（初期配置 `4HPwATDgc/ABMA`、ダイスなし）  すべて期待どおり
- マネー: equity white 0.076、cube no_double 0.098 / double_take -0.171
- 7 ポイント 3-5: equity white -0.017、cube no_double 0.43 / double_take 0.405（値が変わる）。`match` が返る
- クロフォード 6-4: 200、`cube: null`（判断なし）
- 7 ポイントでスコア 7-0: 422 `each score must be 0 .. match_length - 1`
- 7 ポイントで 3-4 + crawford: 422 `the Crawford game needs one side (only) 1 point from winning the match`
- 3-1 を振ったとき: マネー 0.163、7 ポイント 3-5 は 0.076（最善手は同じ）

## 2. PWA（390x844、Chromium、samples/screen1）  期待どおり
- 7 ポイント・3-5 を入れ、写真・四隅・盤面・解析結果の 4 画面すべてで len=7 / w=3 / b=5、欄は表示されたまま。localStorage `match` も同じ
- 写真から解析: `/analyze-photo` のフォームに `match_length=7&score_white=3&score_black=5&crawford=false`
- 解析結果の画面で white を 4 に変更 → `/analyze` が 1 回送られ直し、body に `match_length:7, score_white:4, score_black:5`。結果の先頭は「7 ポイントマッチ 手前 4 対 奥 5。」（equity -0.104 → -0.068）
- 再読み込み: len=7 w=4 b=5 が残る
- マネーに戻す: len=0、スコア欄は非表示、localStorage は `{"length":0,...}`。再読み込みでもマネーのまま
- クロフォード（7 ポイント 6-4、チェックあり）で `synth-cube-photo2-16`（キューブ 16 が black 側）を読む: `/analyze-photo` のフォームは `...score_white=6&score_black=4&crawford=true`。盤面の画面へ進み、alert は
  「クロフォードのゲームではダブルできません。キューブを「中央」にするか、ヘッダーのクロフォードを外してください。」（キューブは 16 のまま）
- 欄の位置（outcome）: `#match` は x16-374（画面幅 390、横スクロールなし）、select と label は重ならず、欠けなし。スクリーンショットでも同じ

## 3. pytest
`uv run pytest analyzer/test_api.py analyzer/test_pwa.py -q` → 64 passed、終了コード 0

## 変更ファイル
git status は、指示の範囲（analyzer/ の README・analysis・app・engine・models・static 5 つ・test 2 つ、docs/PI_CHECKS.md）と `archives/agents/TODO-066/` のみ。範囲外の変更なし。

## 気づいた点（判断は管理者）
- 解析結果の画面の末尾の注記が、マッチでも「勝率とエクイティはキューブなし。」のまま（outcome.png）。マッチのスコアを使っているので文言が合わない可能性がある。実害は未確認
- 同じ画面で、盤面図にキューブ 64 が描かれているのに「キューブなし」。これは screen1 の盤面の読みで、今回の変更で起きたかは未確認
- クロフォードの alert が、サーバーの `analysis_error` 経由かクライアントの送信前の検査かは、この確認では区別していない（どちらも同じ日本語の文）

## 確かめなかったこと
- 壊すと落ちるかの再確認（implementer が実施済み。依頼に無い）
