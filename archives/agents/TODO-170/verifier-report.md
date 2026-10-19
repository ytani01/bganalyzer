# TODO-170 verifier の報告

結論: 指示の 4 点とも一致。食い違いなし。

測定スクリプト: /tmp/claude-649/-home-ytani-work-bganalyzer/960c256d-38f1-4b7f-ac60-64cb492bba16/scratchpad/v.py（コードは直していない）

## 1. 9 組の向きと他のフィールド
- 一致: 9 組すべて、点検の表どおりの手前の色（`bottom_colour`）・home になっている。
  grey-red-top 0/right、tan-black-1 0/left、cork-green 0/left、orange-black 0/left、ajxlol 0/left、p1vm5a 0/left、n8fzpw 0/left、xlkxee 0/left、7qrh2u 1/right（home だけ変更で色は元のまま）
- 一致: 9 組すべて white 15 個・black 15 個（`points` の正負＋bar＋off の合計を測定）。bar・off は全組 0/0。
- 一致: samples/ の 4 組は `git show origin/main:` の元ファイルに「色＝`points` 符号反転・bar/off 入れ替え・`bottom_colour` 反転、home＝行内で左右反転・`home` 反転」を機械的にかけた期待値と、`points`・`read.points`・`bottom_colour`・`home` が完全一致。他のキーの差は note（と cork-green の `fixed_points`）だけ。cork-green の `fixed_points` は元の値を 13−p / 37−p で変換した値と一致（手計算）。`cube`・`dice` は変わっていない。
- 一致: 同じ写真の組どうし（tan-black-1=ajxlol、cork-green=p1vm5a、orange-black=n8fzpw=xlkxee）で `points`・home・`bottom_colour` が同一。
- 一致: collected/ の 5 組には元ファイルが無い（git 管理外）ので、元との差分は取れず、上の不変条件（石の数、samples の同じ写真の組との同一性）で確認した。7qrh2u の `points` は home=right の開始の局面（`[-2,0,0,0,0,5,0,3,0,0,0,-5,5,0,0,0,-3,0,-5,0,0,0,0,2]`）。

## 2. note
- 一致: orange-black（samples）、n8fzpw、xlkxee は「手前は灰色、home=left」。cork-green と p1vm5a の note は「手前は緑・home=left」（cork-green は以前の home の直しが誤りだったと明記）。すべて点検の判断と合う。
- 判断できない（実害は未確認）: orange-black の「手前の色」は点検でも写真を撮った人に確かめるのが確実とされており、本当に灰色が手前かは私は写真を見ていないので分からない。ユーザーが決めた扱い（2026-10-20）どおりに書かれていることだけ確認した。

## 3. 一致件数のスクリプト
`python archives/agents/TODO-170/check_pips.py samples/*.truth.json ~/work/bganalyzer/collected/*.truth.json`（終了コード 0）
- 一致: 色だけ 2 通り **141 / 141**（報告と同じ）
- 一致: 色 × home の 4 通り **126 / 141**（報告と同じ）。不一致の出力の例: `r0woj7 (0, 0) {(0,0): 182, (1,0): 218, (0,1): 218, (1,1): 182}`（同点）
- 注: スクリプトの「色だけ」は `<=` で数えるので、同点も一致に入る。

## 4. accuracy_baseline.json
- 一致: 差分は `photo-orange-black-oblique` の `"home": true` → `false` の 1 行のみ。

## 変更ファイル（`git diff origin/main --stat`）
TODO.md、archives/agents/TODO-170/{check_pips.py,implementer-report.md}、recognizer/accuracy_baseline.json、samples/ の 4 つの truth.json。指示の範囲と合う。recognizer のコード・版は変更なし。

## 確かめなかったこと
- 写真の再点検、`check_accuracy.py`・`evaluate.py`・pytest は指示どおり流していない（CI に任せる）。
