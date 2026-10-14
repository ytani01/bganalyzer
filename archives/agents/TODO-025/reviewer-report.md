# reviewer-report（TODO-025 / PI-032、ブランチ claude/pi-032-commons-cube-dice、未コミットの差分）

対象: `git diff` と未追跡の samples/commons-lg-cube-dice.*、samples/commons-wooden-dice.*、samples/external/galaxy-cube2-near.truth.json。
画像の中身・正解の読み・精度の測り直しは見ていない。

## 要修正

### 1. docs/PI_CHECKS.md:111 / PI-032 の結果を書き込んでいない
- 何が: PI-032 の `- [ ] Pi: （探した結果と足した枚数をここに書く）` がそのまま。差分に docs/PI_CHECKS.md が入っていない。
- 根拠: docs/PI_CHECKS.md:15 の手順 3（「`- [ ] Pi:` を確かめ、`- [x] Pi: 日付、コミット。測った値。OK か` に書き換える」）と、
  CLAUDE.md の「Raspberry Pi で確かめること」（残っている項目を確かめて結果を書き込む）。
  TODO.md の TODO-025 に結果を書いたのは PI-032 の「そのあと」どおりだが、PI_CHECKS.md の側が空のまま。
- 決着させて archives/pi/ へ移すかは、下の 2 の自動マージしない扱いと合わせて管理者の判断（境界線上なので報告だけ）。

### 2. commons-lg-cube-dice が PI-032 の決まりの外で、ai1 の確認を待つことがリポジトリのどこにも書かれていない
- 何が: samples/CREDITS.md:3 と表の行は「Public domain（PD-self）」と正しく書いている。ただし PI-032 の「マージ」の決まり
  （docs/PI_CHECKS.md:109-110: CC0 / CC BY / CC BY-SA 以外があれば自動マージせず、ai1 が見てからマージする）に当たること、
  つまり「この PR は ai1 の確認待ち」という記録が、TODO.md・PI_CHECKS.md のどちらにも無い。
- なぜ: CLAUDE.md の「共同開発」は、方針・決まったことをリポジトリに書くとしている（相手のアカウントから見えないため）。
  PR の説明だけに書くなら、それで足りるかは管理者の判断。PI_CHECKS.md の `- [x] Pi:` の行（上の 1）に
  「lg-cube-dice は PD-self のため自動マージしない」と書けば 1 か所で済む。
- CREDITS.md の書き方自体（「どれも CC BY / CC BY-SA / CC0（lg-cube-dice だけは作者がパブリックドメインにしたもの）」）は事実どおりで、問題なし。

## 検討

### 3. recognizer/README.md:371-373 / キューブの表のまとめが新しい行と合わない
- 何が: 表に 0.17.1 の 2 行（lg-cube-dice、galaxy-cube2-near）を足したが、その下の「キューブのない 17 枚」「7 枚中 5 枚で場所が当たり」
  （0.13.0、x86_64）はそのまま。キューブの無い commons-wooden-dice も足したのに「17 枚」に入っていない。
  表の見出し（:358「2026-10-13、recognizer 0.6.1」）とも版が混ざる。
- 根拠: accuracy_baseline.json で commons-wooden-dice は `"cube": "ok"`（キューブなしを正しくなしと読んだ）。
  まとめの数を直すか、「（0.13.0 の 7 枚の値。PI-032 の 2 枚は含まない）」と断るかは管理者の判断。

### 4. recognizer/README.md:324 / ダイスの表のまとめ「16 枚中、読めるはずの 10 枚で 9 枚当たり」
- 何が: 表に commons-wooden-dice（正解 3-2 で「読まない」）を足したので、読めるはずの枚数が 1 増えたが、まとめは 0.5.0 時点の数のまま。
  上の 3 と同じく、数を直すか版を断るか。

### 5. samples/external/README.md:1-4 / 見出しと冒頭が USBGF の盤面図だけの説明のまま
- 何が: 見出し「外部の盤面図」と冒頭の段落は USBGF の Bray's Learning Curve だけを説明している。
  今回、末尾に Backgammon Galaxy の動画のコマ（盤面図ではなく写真）の節を足したので、冒頭と食い違う。
  :12 の「正解の色の呼び方は…手前（図の下側、赤い駒）が white、奥（白い駒）が black」も USBGF の図の話で、
  galaxy-cube2-near は白い側が手前（truth の note: White = bottom = lilac-white）なので、読み手が混同しうる。
- 冒頭を「外部の画像」程度にし、色の段落を USBGF の節だと分かるようにするかは管理者の判断。

## 好みの範囲

### 6. recognizer/board.py:45 / 版上げ 0.17.0 → 0.17.1
- CLAUDE.md の「そのディレクトリのコードを変える PR で、その方を上げる」の字面どおりで、PI-032（docs/PI_CHECKS.md:106）の指示どおり。問題なし。
- ただし、測るだけの道具（check_accuracy.py・trace_cpu.py）の変更では過去に上げていない（69605a9、5717be9、c12ca22 など）。
  evaluate.py は読み取り（board.py のコメントが挙げる board/position/corners/dice）に入らないので、上げなくても決まりに反するとは言い切れない。
  上げたために cpu_reference.json の meta が書き換わるのは実害なし。指摘ではなく記録として残す。

## 問題が無かった点

- evaluate.py の変更: 正解の cube が無い・`null` は `t.get("cube")` が None で前と同じ。`{"at": "field"}` も、読みの field を black/white に
  直してから比べるので前と同じく一致しない。既存のサンプル 26 枚と external 7 枚で `value` を持つのは今回の 2 つだけ（`rg -l '"value"' samples`）なので、既存の結果は変わらない。
- 呼び出し元（check_accuracy.py:35-41、collected.py:55-57、evaluate.py:64-69）: どれも `cube == cube_want` と `cube_want['at']` だけを使うので意味は変わらない。
  collected.py の `valid()`（:44）は `at` を必須にしているので、`t["cube"]["at"]` の KeyError は起きない。
- コメント（evaluate.py:47-48）は「なぜ at だけか」を書いている。
- accuracy_baseline.json: 2 サンプルの行が足されただけ。26 枚、合計 551 / 624（実測）で README:78 と TODO.md の数字と一致。
- cpu_reference.json: 削除は meta の 3 行（machine・recognizer・cpu）だけで、残りは 2 サンプル分の追加。aarch64 で更新したのは CLAUDE.md の「どの機械で更新してよい」どおり。
- galaxy-cube2-near: 画像は入れず URL と正解だけ（PI-032 の著作権のある画像の決まり、.gitignore:7 で galaxy-cube2-near.png は無視される）。CREDITS.md に載せないのも bray-* と同じ。
- samples/CREDITS.md の大きさの記述（lg-cube-dice は元の 1500px）: `file` で 1500x1000。wooden-dice は 1920x1376 で「長辺 1920px」どおり。
- TODO.md の TODO-025 の結果（2 が 1 枚、4・8・16 が 0 枚、64 が 1 枚、ダイスだけ 1 枚）は README の表・external/README と食い違いなし。
- テスト: evaluate.py には analyzer のテストが無く（`rg evaluate analyzer/test_*.py` が 0 件）、check_accuracy.py の CI が通り道になる。今回の変更の大きさでは追加は要らないと見る。

## 作り込みすぎ

作り込みすぎ: なし（evaluate.py の 1 行は、すぐ上の `cube = info["cube"] and {"at": ...}` と同じ形で、これ以上短くならない）。
