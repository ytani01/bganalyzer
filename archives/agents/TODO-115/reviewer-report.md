# TODO-115 reviewer の報告

対象: `git diff main...HEAD`（ブランチ claude/todo-109-115-117）のうち `analyzer/static/app.js` の読み上げと `analyze()`、
`index.html` のチェックボックス、README の追記。TODO-109・TODO-117 の文言は見ていない。静的に読んだだけで、実機の再生は確かめていない。

要修正: 0 件 / 検討: 3 件 / 好みの範囲: 1 件

## 検討

### 1. 結果の画面から離れても読み上げが続き、止めるボタンが無い
- 場所: `analyzer/static/app.js:468`（`go`）、`:152`（`$("speak").hidden = !(s.step === "outcome" && s.result)`）
- 理由: `go()` も盤面の編集も `stopSpeaking()` を呼ばない（呼ぶのは `setResult` と、今回の `unlockSpeech` だけ）。読み上げ中に「戻る」で
  盤面の画面へ行くと、最後の文まで読み続け、「止める」は隠れている。手で押す読み上げでも前からそうだったが、自動で読むと
  「結果を見てすぐ戻って直す」流れで起きやすくなる。今回の差分の範囲外の前からの挙動なので、直すかは判断が要る。実害は未確認

### 2. 音声合成の解錠が、結果が返ったときの `speechSynthesis.cancel()` で効かなくなる可能性
- 場所: `app.js:1007`（`speechSynthesis.speak(new SpeechSynthesisUtterance(""))`）、`:544`（`setResult` → `stopSpeaking` → `speechSynthesis.cancel()`）
- 理由: 解析の経路では、タップで空の発話を入れたあと、結果が返ると `setResult` が必ず `cancel()` を呼ぶ。iOS の Safari で、
  タップ中の 1 回目の `speak()` で得た許可が `cancel()` のあとも残るかは確かめていない。空文字の発話そのものが iOS で解錠に
  数えられるかも未確認（" " や音量 0 の発話を使う例もある）。Google の声が通っていれば関係なく、ブラウザの声に替わったときだけの話。
  実害は未確認（TODO.md の「スマホ:」の確認で、Google の声を止めた状態でも試すと分かる）

### 3. TODO.md の 2 つ目のチェックに「確かめる」まで入っている
- 場所: `TODO.md:189`（「ブラウザの音声合成に切り替わったときも鳴るか確かめる」に `[x]`）
- 理由: 自動再生の制限は実機でしか確かめられず（同項目 190 行目もそう書いている）、実装の時点で確かめられた中身ではない。
  `~/.claude/CLAUDE.md` の規約では実装できた時点でチェックを入れてよいが、「確かめる」が済んだように読める。確かめる分を
  190 行目の「スマホ:」に寄せるかは判断が要る

## 好みの範囲

### 4. `state.autoSpeak` と関数 `autoSpeak` が同じ名前
- 場所: `app.js:76`、`:1010`
- 理由: 同じ名前で片方は真偽値、片方は「読む」動作。ほかの設定（`collect`・`photoView`・`plies`）は文字列で持っていて、
  これだけ真偽値なのも少し揃っていない。動きには影響しない

## 問題なしと見た点（各 1 行）

- 手で押す「読み上げ」「止める」: トークン `run` で古い `next`/`fallback` が抜けるので、`player` を使い回しても前と同じに動く。
  `fallback` のあと古いハンドラーが残るが、トークンの比較で何もしない。`src` を変えると仕様上、待っているメディアのイベントは捨てられ、
  古い `ended` が新しい `onended` に届くことはない
- 古い `play()` の Promise が `pause()` や `src` の変更で AbortError になっても、古い run の `fallback` はトークンで抜ける
- 無音の `play()` と直後の `startSpeaking`（キャッシュの経路）: `src` を変えると無音の Promise が AbortError になり、`catch(() => {})` で
  捨てられる。新しい `play()` もタップの中なので許可の点でも問題ない。解析の経路では無音（80 サンプル、10 ms）は先に終わり、
  `ended` はハンドラーが null か古い run のもので何も起きない
- 無音の WAV: デコードして確かめた（RIFF、PCM 8 bit・8000 Hz・モノラル、データ 80 バイトすべて 0x80、長さの欄も合う）
- `unlockSpeech` の位置: `analyze()` の最初の `await` より前で、タップの処理の中で呼ばれている。iOS の Safari は要素ごとに
  タップ中の `play()` で解錠し、Chrome はページのタップで許すので、対策として筋は通っている（実機は未確認）
- 解析が失敗した経路: `catch` で `alert` するだけで `autoSpeak()` に届かない。`unlockSpeech` の `stopSpeaking` で前の読み上げは止まる
- キャッシュの経路: `go("outcome"); autoSpeak();` で読む。解析の経路: `setResult` の `stopSpeaking` のあと `go` → `autoSpeak`。どちらも 1 回だけ読む
- オフのとき: `unlockSpeech` も `autoSpeak` も何もしない（前と同じ）
- チェックボックスの表示: `step === "board"` のときだけ出る。`[hidden] { display: none !important; }`（style.css:260）があるので、
  チェックボックスの label の `display: inline-flex`（:305）に負けない。下のバーの高さは ResizeObserver で `--bar-h` に反映される
- 端末への保存: `stored("autoSpeak", ["on","off"], "off")` と `keep` で、既定オフ・開き直しても残る。読みの深さと同じ作り
- 版: `app.py` と `APP_VERSION` がともに 0.65.0。機能の追加なので minor を上げるのは CLAUDE.md の「バージョン」どおり
- 文書: `analyzer/README.md` に追記あり。ほかの文書（README.md、docs/raspi.md、docs/HANDOVER.md）に古くなる記述は無い（`rg 読み上げ` で確認）
- テスト: `test_pwa.py` の `test_photo_view_is_a_checkbox` のような文字列の照合テストは足していないが、その種のテストは壊すと落ちる強さが
  弱く、確認は TODO.md の「ローカル:」の行に任せている。足さなくてよいと見た
- コメント: `player` のコメントは「なぜ 1 つを使い回すか」を書いている

## 作り込みすぎ

- `app.js:1010`: shrink: `autoSpeak` の `state.result` の判定は、2 か所の呼び出し元とも `state.result` が必ずある（キャッシュの経路は条件で、
  解析の経路は `setResult` の直後）。`state.autoSpeak` だけでよい
- net: -0 lines possible（判定 1 つ分の短縮だけ。ほかは削れるものなし）
