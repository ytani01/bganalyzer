# verifier 報告（TODO-139）

依頼: archives/agents/TODO-139/verifier-request.md
対象: ブランチ claude/edge-black の未コミットの変更（recognizer/）

## 結果

| # | 内容 | 結果 |
|---|------|------|
| 1 | 直した版で t0480x の board.py | 期待どおり（下に出力） |
| 2 | PEAK_REL を 0.25 に戻す | 期待どおり（19 が空に戻る） |
| 3 | 足した円の連鎖の `len(chain) >= 2` を `>= 99` | 期待どおり（12 が空に戻る） |
| 4 | `0.3 * pitch < depth` を `-9 * pitch < depth` で wooden-dice | **期待と違う**（point 11 が got -3。期待は got -4） |
| 5 | 戻した版で 3 サンプル | 期待どおり（13/24、24/24、24/24、point 11 got -3） |

## 1. 直した版（board.py、t0480x）

```
 13 14 15 16 17 18   19 20 21 22 23 24
 5W  .  .  . 3B  . | 5B  .  .  .  . 2W
 5B  . 1B  . 3W  . | 5W  .  .  .  .  .
 12 11 10  9  8  7    6  5  4  3  2  1
bar W0 B0  off W0 B1  pips W167 B134
```

19=5B、12=5B、10=1B、17=3B、1 は空。期待どおり。終了コード 0。

## 2. PEAK_REL = 0.25（radial.py）

上の表で 19 の列が空になった（上段の 19 が `.`）。期待どおり。
終了後、radial.py は保存しておいた版に戻し、`git diff` の 2 行の変更に戻った。

## 3. `len(chain) >= 99`（checkers.py）

下段の 12 が `.` になった（`5B` から変化）。期待どおり（空に戻る）。
終了後、checkers.py は保存しておいた版に戻した。

## 4. `-9 * pitch < depth`（checkers.py）で wooden-dice

変更は 1 箇所（checkers.py 277 行目。`rg` で 1 件だけ一致）。出力:

```
commons-wooden-dice.truth.json: 13/24 points correct, bar ok, home guess ok (+2.4), dice not read (read None, truth [3, 2]), cube ok (read None, truth None)
   point  1: truth -2  got +0
   point  6: truth +5  got +3
   point  7: truth +0  got +1
   point  8: truth +3  got +0
   point 11: truth +0  got -3
   point 12: truth -5  got +0
   point 13: truth +5  got +0
   point 17: truth -3  got +0
   point 18: truth +0  got -1
   point 19: truth -5  got -4
   point 24: truth +2  got +0
```

期待は point 11 が got -4（元の版では -3）だったが、got -3 のままだった。
この出力は、直した版（5 の 1 行目）の wooden-dice の出力と行単位で同じである。
つまり、この変更は wooden-dice の結果を一つも変えていない。
期待との食い違いの原因は確かめていない（推定もしていない）。
依頼の期待値が違うのか、この変更が効く条件が別にあるのかは、判断できない。
終了後、checkers.py は保存しておいた版に戻した。

## 5. 戻した版の 3 サンプル

```
commons-wooden-dice.truth.json: 13/24 points correct, ... (4 と同じ出力。point 11 got -3)
commons-dark-homeleft.truth.json: 24/24 points correct, bar ok, home guess ok (-17.7), dice ok (read None, truth None), cube ok (read None, truth None)
screen1.truth.json: 24/24 points correct, bar ok, home guess ok (-18.0), dice ok (read [4, 2], truth [4, 2]), cube ok (read centre, truth centre)
```

期待どおり（13/24、24/24、24/24、wooden-dice の point 11 は got -3）。終了コード 0。

## 変更されたファイル

`git status` は依頼時と同じ。M は recognizer/README.md、board.py、checkers.py、radial.py、tune.py。?? は archives/agents/TODO-139/。
`git diff -- recognizer/` は、検証の前に保存した差分とバイト単位で一致した（作業ツリーは検証後も元どおり）。
変更の範囲は依頼の「直し」の範囲と合っている（board.py はバージョン 0.27.1、radial.py は PEAK_REL、checkers.py は ALIKE_SUPPORT と円の連鎖、tune.py は PARAMS に ALIKE_SUPPORT の追加、README.md は説明と記録の追記）。
ただし、依頼は「変更の範囲の確認」を求めていないので、この点は読んだだけで、テストはしていない。

## 確かめられなかったこと

- 全サンプルの evaluate と check_accuracy は依頼どおり流していない。
- 項目 4 の食い違いの原因は、切り分けしていない（依頼の範囲外。判断は管理者）。
- 作業ツリーの一時的な書き換えは `sed` で行い、終了後は保存した版から `cp` で戻した。

## 判断が要る点

- 項目 4 の期待値（point 11 が got -4）が、この変更で実際に出るかどうか。出ないなら、依頼の期待が誤りか、`-9 * pitch` の変更が効かない条件があるか。どちらかを管理者が決める。
