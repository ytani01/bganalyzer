# TODO-027 verifier 報告（eb49710、ブランチ claude/todo-027-dark-checkers-impl）

測り方は依頼どおり（`uv run -q --no-project --python 3.12 --with opencv-python-headless --with numpy python ...`、終了コードはすべて 0）。コードは変更していない。

## 1. samples 23 枚
- ブランチ合計 505、main 492。期待どおり。
- dark-homeleft 12 → 22、set-cube-dice 12 → 15。ほかのサンプルの正しいポイント数は同じ。
- bar・home guess の ok/WRONG、dice、cube の判定は 23 枚とも main と同じ（set-cube-dice の bar wrong も main と同じ。leather-cups の dice WRONG も同じ）。悪くなったものは無い。
- 正しい数は同じだが、誤りの中身が変わったもの（参考、実害は未確認）: photo2 の point 19（main は +0、ブランチは -4。truth -5 でどちらも誤り）。home guess の数値は dark-homeleft -1.6 → -14.7、set-cube-dice +2.2 → +5.4、photo2 +8.8 → +13.1、rollup-oblique +18.3 → +27.7 と変わった（符号・ok は同じ）。

## 2. collected/user-*.truth.json
依頼は 4 組だが、ファイルは 5 組あった（追加の `user-1791971847586-sj1vrx` は 22 → 22 で同じ）。
| ファイル | ブランチ | main |
|---|---|---|
| user-1791923350916-h8ilqt | 24 | 23 |
| user-1791941311542-5wxq9t | 19 | 19 |
| user-1791967712086-l9azfe | 14 | 15 |
| user-1791968461325-3wo2ot | 18 | 18 |
- 4 組の合計はブランチ 75、main 75。「main（75）を下回らない」は満たす。期待の 24・19・14・18 とも一致。
- 食い違い: user-1791967712086-l9azfe は main 15 → ブランチ 14 で 1 つ悪くなっている（別の 1 組が 1 つ良くなって相殺）。

## 3. 円の重複
`archives/agents/TODO-027/dup_hough.py` を作成（`board.cv2.HoughCircles` の結果を axis=1 で 2 回つなげる）。
commons-rollup-oblique と commons-dark-homeleft を `evaluate.run` で読み、例外なし（OK 2 件、終了コード 0）。

## 4. 壊すと落ちるか
scratch に recognizer をコピーし `TEX_HIDDEN = 0`、`TEX_SHOWN = 100` に変更して samples 23 枚を測定。
- dark-homeleft 12/24（22 より下がった。main と同じ値）、set-cube-dice 12/24（15 から下がった）。
- 他のサンプルは通常のブランチと同じ。狙った 2 枚だけが落ちた。

## 確かめられなかったこと
- 特になし。dup_hough.py で重複が実際に Hough 呼び出しごとに入ったことは、置き換えが cv2 モジュールの属性に対するものであることからの推定（呼び出し回数は数えていない）。

# 2 回目（コミット 0f28503）

依頼ファイルの 1〜4 を同じやり方で測り直した（終了コードはすべて 0）。dup_hough.py は変更なし。
- 1. 期待どおり。合計ブランチ 503、main 492。変わるのは dark-homeleft 12→20、set-cube-dice 12→15 だけ。bar・home・dice・cube の判定は 23 枚とも main と同じ（評価行を home guess の数値を除いて diff。差は上記 2 行のみ）。
- 2. 期待どおり。ブランチ 24・19・14・18・22 = 97、main 23・19・15・18・22 = 97。下回らない。l9azfe は前回と同じく main 15 → ブランチ 14（h8ilqt の 23 → 24 と相殺）。
- 3. 期待どおり。rollup-oblique・dark-homeleft とも例外なし。
- 4. 期待どおり。TEX_HIDDEN=0・TEX_SHOWN=100 で dark-homeleft 12/24、set-cube-dice 12/24。ほかは通常のブランチと同じ（rollup-oblique 13 など）。
- 5. 期待どおり。`git diff origin/main` で accuracy_baseline.json の変更は dark-homeleft 12→20 と set-cube-dice 12→15 の 2 行だけ。.github/workflows/accuracy.yml は差分なし。
  参考: baseline の case-dice 19・leather-cups 20 は、この Pi の測定（18・19）と違う。ただし main と同じ値で、今回の変更ではない（x86_64 と Pi の差と推定、未確認）。
