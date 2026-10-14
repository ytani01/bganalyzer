# verifier 報告（PI-032）

## 結果
- check_accuracy.py: 終了コード 0（最後 `points: 551/624 (baseline 551)`）
- trace_cpu.py check: 終了コード 0（`0 of 26 samples read differently` / `same as the reference: every step of every sample`、aarch64、recognizer 0.17.1）

## 1. 正解ファイル（画像と目視で突き合わせ）
- commons-lg-cube-dice: points（-2@1, +5@6, +3@8, -5@12, +5@13, -3@17, -5@19, +2@24）、home right、bottom_colour 0（手前=暗い駒）、dice null（両者のサイコロが盤上に 2 組）、cube 64 左トレイ中央 すべて一致。四隅は遊戯面を指している
- commons-wooden-dice: points 一致、home right、bottom_colour 0（濃い胡桃）、dice [3,2] 一致、cube null 一致。四隅は枠の内側を指している
- galaxy-cube2-near（URL から取得。2500x1131）: points 一致、home right、bottom_colour 1（手前=薄い紫白）一致、cube 2 が手前左トレイ（at white は画像から確認できない。所有者は目視で断定できないが、手前側で矛盾なし）。左 2 隅は遊戯面の角、右 2 隅は画像外 → 前提どおり
- 食い違いなし

## 2. evaluate.py の直し
- 元写真 commons-set-cube-dice の truth を複製し cube に "value": 2 を追加、image は絶対パス
- 直した版: `cube ok (read centre, truth centre)`
- 直しを戻した版（scratchpad のコピー、`(cube, t.get("cube"))` に戻す）: `cube WRONG (read centre, truth centre)`
- 直しは効いている。リポジトリのファイルは変更していない

## 3. CREDITS.md（Commons API）
- Backgammon_lg.jpg: Artist Ptkfgs、License `pd`（Public domain）→ 一致
- Wooden_backgammon_(27095563797).jpg: Artist The Unwinder（Flickr）、CC BY-SA 2.0 → 一致

## 変更ファイル
git status は TODO.md, archives/pi/index.md, docs/PI_CHECKS.md, recognizer/{README.md, accuracy_baseline.json, board.py, cpu_reference.json, evaluate.py}, samples/{CREDITS.md, external/README.md}、新規: archives/agents/TODO-025/, archives/pi/PI-032…md, samples/commons-{lg-cube-dice,wooden-dice}.{jpg,truth.json}, samples/external/galaxy-cube2-near.truth.json。
指示の範囲外のファイルかどうかは、PI-032 の指示文を受け取っていないため判断できない。recognizer/board.py の変更内容（バージョンなど）は見ていない。

## 判断できなかったこと
- galaxy の cube "at": "white" が正しいか（画像から所有者は読めない。実害は未確認）
- lg-cube-dice の四隅の画素精度（指示どおり測っていない）
