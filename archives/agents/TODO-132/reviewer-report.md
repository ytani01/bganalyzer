# TODO-132 reviewer の報告

対象: `git diff main`（ブランチ claude/todo-132-speech-kana、未コミット。TODO.md・analyzer/app.py・analyzer/static/app.js・analyzer/static/result.js・analyzer/test_pwa.py）

要修正: 0 件 / 検討: 0 件 / 好みの範囲: 2 件

## 要修正

なし

## 検討

なし

## 好みの範囲

1. `analyzer/static/result.js:157-160` / `kana()` は数字でない文字列を渡すと `じゅうundefined` を返す
   （`moveToSpeech("x/off")` → `じゅうundefinedから上がり`、`0/off` → `から上がり`。node で実測）。
   直す前は文字列をそのまま返していた。gnubg の手の表記は 1〜25・bar・off だけなので、届く経路は無い。
   実害は未確認（届かないと読んだだけ）。

2. `analyzer/README.md:97` / 読み上げの説明に「目とポイントの番号はかなで読む」が無い。
   古くなった記述ではない（数字で読むとは書いていない）ので、足すかは任意。

## 問題なしの点

- kana(): 1〜30 を node で実測。1 いち〜9 きゅう、10 じゅう、14 じゅうよん、17 じゅうなな、19 じゅうきゅう、20 にじゅう、24 にじゅうよん、25 にじゅうご。枚数の 2〜15 も同じ式で正しい
- 画面の HTML に影響なし: html() は `esc(m.move)` と `dice.join("-")` のままで、kana を通らない。test_result_html の `<li ...>bar/22* 13/8(2) 6/off` と「ダイス 3-1」の assert も残っている
- speechText で数字が残る経路: `rg -n '\$\{' analyzer/static/result.js` の 110〜152 行を見た。数字を入れるのは roll（126 行）と moveToSpeech だけで、どちらも kana を通る。cubeText・luckWords・standingToSpeech・NAME は語だけ
- 1 文の長さ: 最も長い手（4 つともヒットの 2 桁の手、ゾロ目）で 88 文字。`/speech` の上限 200 文字に収まる（node で実測）
- 版: analyzer 0.73.1 → 0.73.2（直し）、`APP_VERSION` も同じ。recognizer は触っていない。CLAUDE.md の「バージョン」どおり
- tools/pi_ui_check.py の check_speech（`\d+\s*ピップ` などを見る）は数字が減る方向なので影響なし
- テストは壊すと落ちる形: `n >= 20` → `n > 20`（20 が じゅう になる）、`n < 10` → `n <= 10`（10 が undefined）、roll を数字に戻す、枚数の kana を外す、のいずれも既存か新しい assert が落ちる（式から読んだもの。テストは流していない）
- コメントは「なぜ」（声によって 2 を に／ツーと読む）を書いている。moveToSpeech の例のコメントも新しい出力に合わせてある
- 範囲: 指示に無い変更なし。TODO.md はチェックを入れただけ

## 作り込みすぎ

なし（kana は 4 行、テーブル 1 つ。`Number(n)` は比較で暗黙に変換されるので無くても動くが、1 語なので挙げない）。Lean already. Ship.
