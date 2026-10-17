# TODO-077 レビュー（reviewer）

対象: コミット 3226763（`recognizer/checkers.py` の `column_texture`、版、README、基準）。
要修正: 0 件。検討: 4 件。好みの範囲: 1 件。

実測（`archives/agents/TODO-077/` ではなく作業用の一時スクリプトで、`column_texture` を
新旧（`TEX_MIN_COVERED=inf` を旧とみなす）両方で呼んで、ラベルの違いだけを出した。photo5 と commons-leather-cups の 2 枚だけ）:

- photo5: 4 回の呼び出しすべてで、代替の基準を使ったのは **bottom の深さ 1 の行だけ**。
  増えたラベルは hidden が 7 列（0,2,4,5,6,7,8）、**shown が 4 列（1,3,9,10。2〜4 回目は 1,3,9）**。読み違い 0
- commons-leather-cups: 増えたラベル 0（4.0 で捨てている）。読み違いは 9 ポイントで、基準の 15 と同じ

## 検討

### 1. `recognizer/checkers.py:88-90` / 代替の基準の行では、shown が必ず 3 列前後付く。`detect_checkers` の候補の除外に効く

- 何が問題か: 75 パーセンタイル（12 列なら 9 番目と 10 番目の間）を基準にすると、上位 3 列は必ず
  `ratio > 0.84 * p75` になり "shown" になる。中央値のときの前提（「ほとんどの所は空いている」= docstring）が
  無い行なので、上位 3 列が本当に空いている保証は無い。docstring と `detect_checkers` のコメント
  （checkers.py:219-221）にあるとおり、斜めの写真では駒の山の側面も縦のエッジに見える
- 壊れ方の筋: 山の側面で比が上位に入った列の候補が `drop_shown=True` の呼び出し（board.py:134・141・146）で
  落ちる。救うのは「同じ列・同じ側に shown でない円が 2 つ以上」のときだけなので、**2 個の山で深さ 1 が shown、
  深さ 0 だけ shown でない**、という形だと深さ 1 の駒が戻らない。`add_hidden_stacks` 側は
  「深さ 0 が shown なら足さない」（checkers.py:278）なので、深さ 0 が代替の行になったときに shown が付くと
  隠れた山を拾わなくなる、という逆向きの効き方もありうる（photo5 では深さ 0 は代替を通らなかった）
- 根拠: 上の実測で photo5 の bottom 深さ 1 に shown が 4 列増えた（読みは変わらず）。他のサンプルで
  代替を通る行があるか、そこで候補が落ちたかは**未確認**（全サンプルは流していない）。実害も未確認。
  境界線上の判断なので報告だけ

### 2. `recognizer/checkers.py:53` / 4.0 は 3.2（leather-cups）と 4.7（photo5）の 2 点の間に置いた値

- 何が問題か: 下（3.2）とは 0.8、上（4.7）とは 0.7 の幅しか無く、根拠は 2 枚。コメントに 2 つの値を
  書いてあるのは良い（なぜ 4.0 かが読める）
- 根拠: コメントと依頼文の値。他のサンプルの行の 75 パーセンタイルが 3〜4.7 の間にどれだけあるかは**未確認**。
  CI の accuracy が全サンプルで見ているので、今の基準の範囲では足りている。境界線上の判断なので報告だけ

### 3. `recognizer/checkers.py:65`・`54`・`55` / docstring と TEX_HIDDEN・TEX_SHOWN のコメントが「中央値」のまま

- 何が問題か: docstring は「compare ... with the median of the row (most spots are empty)」、TEX_HIDDEN は
  「share of the median」。代替の行では 75 パーセンタイルと比べ、「ほとんど空いている」も成り立たない
- 根拠: 差分で変えたのは 88-90 行だけで、65 行の docstring と 54-55 行は元のまま（`git show 3226763`）

### 4. `recognizer/tune.py:37` / PARAMS に `checkers.TEX_MIN_COVERED` が無い

- 何が問題か: 同じ組の `TEX_MIN`・`TEX_HIDDEN`・`TEX_SHOWN` は試す定数の一覧に入っている。新しい定数だけ漏れている
- 根拠: tune.py:37。`TEX_MIN_COVERED` は既定引数に使われていない（実行時に読む）ので、足せば試せる

### 文書との整合（検討に含めない、参考）

- `recognizer/README.md:513-522`「四隅を固定して読む（TODO-084、recognizer 0.23.0）」の表で photo5 の
  「合わせ直す（既定）」が 22 のまま。見出しに 0.23.0 と書いてあるので誤りではないが、49 行目の 24 と並ぶ。
  「固定する」の 16 が変わったかは**未確認**
- `recognizer/README.md:57`（collected 17 枚、0.23.0 で 347）は、基準の差分が photo5 だけなので数は変わらないはず
  （collected も基準に 17 件入っている）。版の書き方はそのままで問題ない
- docs/ に TODO-077 や photo5 の 22 を書いた所は無い（`rg -n "photo5|TODO-077" --glob '!archives/**'`）

## 好みの範囲

### 5. `recognizer/checkers.py:88-91` / nan を代入して次の if に落とす書き方

作り込みすぎの節の shrink と同じ。nan を使う書き方は動く（`not nan >= x` は True）が、
「TEX_MIN_COVERED ≥ TEX_MIN」を暗に前提にしている（逆にすると、75 パーセンタイルが両者の間の行は
代替の基準を通ったのに 91 行で捨てられる）。下の形なら前提が要らず、意図もそのまま読める。

## 作り込みすぎ

- `checkers.py:L88-91: shrink: nan を代入して 2 つ目の if で捨てる 4 行。` 次の形で 3 行（91 行の 2 つ目の判定は要らなくなる）:

  ```python
  if not med >= TEX_MIN:   # most spots may be covered: the upper quarter, if clear (photo5's bottom row, TODO-077)
      med = float(np.nanpercentile(ratio, 75))
      if not med >= TEX_MIN_COVERED:   # the triangles' sides do not stand out here
          continue
  ```

net: -1 lines possible.

## 問題なし（1 行ずつ）

- 版: recognizer 0.23.0 → 0.23.1（見落としの直し = patch）、`board.py` の `__version__` だけで analyzer は触っていない。CLAUDE.md の「バージョン」に合う
- `recognizer/README.md:49`: photo6 の行（「18（recognizer 0.22.3。0.22.2 は 10。…）」）と同じ書き方で、前の版の値も残している
- 基準: `accuracy_baseline.json` は photo5 の 1 行だけ。CLAUDE.md の「良くなったときは同じ PR で書き直す」に合う
- テスト: 単体テストは無いが、photo5 の基準 24 と leather-cups の基準 15 が、代替を消したとき・4.0 の捨てを消したときに
  CI の accuracy で落ちる形になっている（後者は依頼文の「11 ポイントに偽の -4」による。外して落ちるかは未確認）
- 行の長さ: 88 行は 125 文字で、ファイルの最長（134）の範囲内
- 範囲: `archives/agents/TODO-077/tex.py` と TODO.md のチェック以外に指示に無い変更は無い
