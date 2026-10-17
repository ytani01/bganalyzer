# TODO-113 verifier 報告（HEAD d1d5329、a0.71.0 · r0.24.0）

使ったスクリプト: `archives/agents/TODO-113/verify_board_parts.py`（項目 1〜6。live_view の窓に CDP でつないで実行）

## 項目 1〜6（実測値）
1. `[data-part]` の種類は match×3・home×2・colour×2・roll×2・cube×1 の要素。各 1 つをタップ
   - home: right -> left、盤面図の SVG が変化（鏡写し）、もう一度タップで right に戻る: 合う
   - colour: bottomColour 1 -> 0、もう一度で 1: 合う
   - match / cube / roll: 開いたシートはそれぞれ #sheet-match / #sheet-cube / #sheet-roll だけ（他は不可視）: 合う
   - match: 長さ 0 -> 3 で図の文言が「3 ポイントマッチ ▾」、5 で「5 ポイントマッチ ▾」、スコア 2 点/1 点: 反映された
   - cube: 白へ -> state.cube.at "white"、図の文字列にキューブ位置の変化あり（図の文字列は "2" が末尾に出る形に変わった）: 反映
   - roll: 3・5 -> 図に "3" "5" が出る: 反映。空に戻した
2. シートを開いたまま: #sheet-match の bottom = 731、#actbar の top = 731（接している。重ならない）。#analyze は disabled=false で、中心の点に elementFromPoint で届く（押せる状態）。実際には押していない
3. ✕ で match / cube / roll の各シートが閉じた。cube シートを開いたまま #back で写真の画面へ移り、「手で入力」で戻ると state.sheet = null、3 枚とも不可視: 合う
4. アンリミテッド（length 0）で図に「アンリミテッド ▾」あり。ダイスが空で `.die-q` が 2 つ（テキスト "?" 2 つ）: 合う（点線の見た目そのものは見ていない）
5. 色を 1 -> 0 に変え、再読み込み、「手で入力」で bottomColour = 0 のまま。1 に戻した: 合う
6. `#result-svg` と `#photo-svg` の `[data-part]` は 0 個。`#home-pick` は DOM 全体で 0 個（盤面の画面も四隅の画面も、この確認の時点の DOM に無い）: 合う。ただし四隅の画面を実際に出して見てはいない

## 項目 7: tools/pi_ui_check.py（BG_CDP あり・なしで各 1 回、終了コード 1。同じ結果）
```
FAIL double: dice=None best=None cube-help='黒の人のダブルを判定します。' alerts=[]
FAIL speech: TimeoutError: Page.click: Timeout 30000ms exceeded.
FAIL export: files=['user-20261018-0437.png', 'user-20261018-0437.truth.json'] points_match=True dice=None alerts=[]
FAIL export-denied: files=[...] points_match=True dice=None alerts=[]
FAIL collect: TimeoutError: Page.click: Timeout 30000ms exceeded.
```
collect 以外の 4 つ（double・speech・export・export-denied）も落ちた。どれも `dice=None` か `Page.click` のタイムアウトで、写真を読んだ後に `BgApp.rolled()` が空になっている。
この変更で起きたのか前からかは未確認（main での実行はしていない）。推定: read_photo が追加した `BgApp.update({homePick, bottomColour})` の影響かもしれないが、切り分けていない。実害は未確認。

## 項目 8: tools/ui_snapshot.py record
エラーなく終了、`64 snapshots` を /tmp 側（scratchpad）の a.json に記録。

## 変更ファイル
`git status`: 作業ツリーは、私が足した `archives/agents/TODO-113/verify_board_parts.py` 以外に変更なし（コードは直していない）。

## 後片付け・判断できないこと
- 窓の始める前の値は、最初の実行が途中で落ちて記録が残らなかった。確実に分かるのは bottomColour=1・home=right・collect=off・autoSpeak=on。マッチは、2 回目の実行の開始時に localStorage が {5, 2点, 1点} だったので、元は長さ 5（2/1）だったと推定して戻した（確証なし。途中で 0 や 3 に変えたのは確かで、その後 5 / 2 / 1 に戻した）。窓は写真の画面にある
- シートの下端と #actbar の上端が「同じ 731」で、「より上」か「接する」かの境界は判断しない
- 項目 1 のキューブの反映は、図の文字列の変化で見た。見た目（位置・向き）は見ていない
