# verifier 報告 TODO-031（HEAD 38d80a3）

## 1. pytest（docker、指定のコマンド）
`1 failed, 38 passed, 6 skipped`。落ちたのは想定どおり `test_version_reports_both_parts_and_commit`
（`FileNotFoundError: [Errno 2] No such file or directory: 'git'`）だけ。`test_4xx_reason_is_logged` は通過。

## 2. 壊すと落ちるか（git archive HEAD のコピー、scratchpad/w。本体は未変更）
ベース: `test_4xx_reason_is_logged` 1 passed。
- (a) validation のログに `e['input']` を足す: FAILED（`assert 'secret-value...`）
- (b) `%r` -> `%s`: FAILED（`assert "POST /analyz...`）
- (c) log_http_error のログ行を `pass` に置換: FAILED（`assert "POST /analyz...`）
  （行を消すだけだと if 本体が空で構文エラーになり収集で落ちるので、`pass` にした）
3 通りとも狙ったテストが落ちた。

## 3. 実際のログ（port 8001、読み取り専用マウント、コンテナ tmp-v031。停止済み）
1. `-F image=@README.md -F corners=1,...,8` -> 422 `{"detail":"could not decode image"}`
   log: `WARNING:  POST /analyze-photo -> 422: 'could not decode image'`
2. 上に `-F plies=abc` -> 422、
   log: `WARNING:  POST /analyze-photo -> 422: body.plies: Input should be a valid integer, unable to parse string as an integer`
   ログに `abc` は出ていない。
- 参考（変更前と同じ挙動のはず。比較はしていない）: レスポンス本文には `"input":"abc"` が入る。ログではなくレスポンスなので範囲外。

## 範囲・未確認
- 作業ツリーは clean（HEAD のコミット済み）。git diff main の範囲は未精査（指示の確認項目外）。
- 本番 bganalyzer-app-1 には触っていない。
- イメージ bganalyzer は以前のビルドで、/repo のコードを使ってテスト・起動した（import 元は /repo/analyzer）。
