# verifier 報告（TODO-012、recognizer 0.5.1、Raspberry Pi）

コードと文書は変更していない。写しと出力は scratchpad（a/ = refine_tips の節を `if False:` に、b/ = `and depth > 0.3 * pitch` を削除）。

## 1. evaluate.py（samples/*.truth.json 全 19 枚）終了コード 0（約 1 分 22 秒）
直す前（evaluate-pi-0.5.0.txt）と見出し行（N/24・bar・home guess・dice）を diff: 差は leather-cups の 1 行だけ。一致。
- 前: `commons-leather-cups: 9/24, bar ok, home guess ok (+8.6), dice ok (read None, truth None)`
- 後: `commons-leather-cups: 19/24, bar ok, home guess ok (+19.5), dice WRONG (read [3, 3], truth None)`
- 他の 18 枚は同じ。一致。

## 2. samples/external（7 枚）前後比較
`git stash` で外して測定 → `git stash pop` で復元（`git diff --stat`: TODO.md, recognizer/README.md, recognizer/board.py の 3 ファイル、+44 -17。測定前と同じ）。
before と after の出力は全文 diff 無し。一致。値: 106=24, 107=22, 108=24, experts-105=24, experts-106=24, inter-105=24, inter-106=24（計 166/168）。

## 3. 壊すと落ちるか
| 版 | leather-cups | rollup-oblique |
|---|---|---|
| 現行 | 19 (+19.5) | 13 |
| (a) refine_tips の節を無効 | **13** (+4.0)、dice は ok（読まない） | 13 |
| (b) depth 条件を削除 | 19 (+19.5) | **11** (+18.2) |
- (a): 期待どおり 19 から下がる。ただし 19→13 で、README の「9 → 18/24」（節だけでの値）の 18 とは別の測り方（a は弱い円の節は有効のまま）。9→18 の内訳は測っていない。
- (b): 期待どおり rollup-oblique 13→11。leather-cups は変わらず。一致。

## 4. 文書と実測
- Commons 11 枚（case-dice・nardy・rollup を除く commons-* 計 11 枚）の合計: 直す前 232、後 242。README 表の「232 → 242」と一致。
- ダイス表 leather-cups 行・「0.5.1 から白の 3-3 を読む（正解は『読まない』）」: 実測 dice WRONG [3,3] と一致。16 枚の dice WRONG は samples 内で leather-cups の 1 件のみ。
- 「Pi で 9 → 19」「home guess 差 19.5」（README ホーム推測の節）: 一致。dark-homeleft の +/- 差は 1.6 のまま（-1.6）。一致。
- TODO.md の「9→19/24」: 一致。

## 測っていない・判断できない
- README の「このしきい値は余裕が小さい（leather-cups で足す円は 0.33、rollup-oblique で外す円は 0.19）」の 0.33 / 0.19: 円のスコアを出力していないので未確認（(b) で rollup が 11 に下がることだけ確認）。
- README の「9 → 18/24」（refine_tips だけの効果）と「18 → 19」: 中間の版は作っていない。未確認。
- ダイス表の「0.5.0 までは白も 1 つだけ確かだった」は 0.5.0 の出力に dice の詳細が無く未確認（0.5.0 は dice ok = 読まない、は確認済み）。
- 「余裕が小さい」かどうかの評価は判断しない。
