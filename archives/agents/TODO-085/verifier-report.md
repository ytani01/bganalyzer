# TODO-085 確認報告（verifier）

対象: ブランチ `claude/todo-085-row-hidden-by-wall-fix`、recognizer/geometry.py の refine_tips。

## 1. evaluate.py の points correct（各 1 回）

| サンプル | 期待 | 結果 | 判定 |
|---|---|---|---|
| photo6 | 18 | `photo6.truth.json: 18/24 points correct, ...` | 一致 |
| collected-er0y2w | 20 | `collected-er0y2w.truth.json: 20/24 points correct, ...` | 一致 |
| photo5 | 22 | `photo5.truth.json: 22/24 points correct, ...` | 一致 |

- 終了コードは記録できなかった。シェルが zsh で `${PIPESTATUS[0]}` が空になり、出力だけ取れた。出力には Traceback や Error は無かった。

## 2. 壊すと落ちるか（photo6 のみ、1 回）

- geometry.py の `if lb < ROW_SHORT * lt:` を指示どおりの条件式に一時的に書き換えて実行。
- 結果: `photo6.truth.json: 10/24 points correct, ...`、終了コード 0。期待の 10 と一致。
- 出力の抜粋（間違えた点）:
  ```
  point  1: truth +4  got -3
  point  5: truth -2  got +1
  point  6: truth -1  got +0
  point  7: truth -3  got +2
  point  8: truth -3  got +2
  point  9: truth -2  got +1
  point 15: truth +2  got +0
  point 17: truth -1  got +0
  point 18: truth +4  got -3
  point 19: truth +1  got +0
  point 20: truth +2  got -1
  point 22: truth +1  got +0
  point 23: truth +1  got +0
  point 24: truth -3  got +2
  ```
- 書き換え後に `git checkout recognizer/geometry.py` で戻した（"Updated 1 path from the index"）。`git diff -- recognizer/geometry.py` は 0 行。`git status --short` は空。
- 注: 書き換えの出力は `/tmp/x` に一時保存した（リポジトリの外。管理者の指示は書いていなかったが、スクラッチパッドを使うべきだった）。

## 3. 基準とバージョン

- `recognizer/accuracy_baseline.json`: photo6 は 18、collected-er0y2w は 20。一致。
- `recognizer/board.py` の `__version__`: `"0.22.3"`。一致（main では 0.22.2）。

## 変更ファイルと範囲（`git diff --stat main...HEAD`）

- TODO.md（6 行）
- archives/agents/TODO-085/README.md、probe_tips.py、reviewer-report.md（作業記録）
- recognizer/README.md（10 行）
- recognizer/accuracy_baseline.json（3 件の値）
- recognizer/board.py（version のみ）
- recognizer/geometry.py（refine_tips と定数の説明。上の段の届き方の条件は従来どおり）

指示の範囲と合っている。指示に無いファイルの変更は見当たらなかった。

## 判断が要る点（報告のみ。直していない）

- **collected-er0y2w は 21 から 20 に下がった。** 変更前の基準は 21。今回の変更で 1 点悪くなり、基準を 20 に下げて合わせている。CLAUDE.md は「良くなったとき」に基準を書き直すと定めており、悪くなった分を基準で受け入れてよいかは管理者が決める。
- photo5 は 22 で基準と一致した。ただし `home` は `guess wrong (+16.1)` と出ている。基準は `home: false` で一致している。判定は変わっていない。

## 確かめられなかったこと

- 全サンプルの精度（CI が見る範囲）は流していない。指示どおり。
- 終了コードの記録は 1 のうち 3 件とも欠けた（上記）。
- `recognizer/README.md` の表の数値は確かめていない。
