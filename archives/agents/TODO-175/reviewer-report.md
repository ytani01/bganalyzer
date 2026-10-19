# TODO-175 reviewer 報告

対象: `git diff origin/main...HEAD`（1abc3ec）。測ったのは下の 5 例だけ（全サンプル・check_accuracy は流していない）。
測定スクリプト: `/tmp/claude-649/-home-ytani-work-bganalyzer/c6c11ee0-ca78-47d7-88b6-2bd508532d0c/scratchpad/cmp.py`
（origin/main の corners.py とこのブランチの corners.py で `find_corners` を流し、正解の四隅からの距離 TL/TR/BR/BL を px で出す。
「painted」は `import_collected.paint` を正解の四隅で掛けたもの、つまり `samples/` に入る形）。

| 写真 | main | このブランチ |
|---|---|---|
| hedmzy（collected/ の元の写真） | [51, 1, 0, 11] | [19, 7, 0, 11] |
| hedmzy painted（samples/ に入る形） | [42, 10, 2, 12] | [42, 10, 2, 12] |
| t0480x（collected/ の元の写真、TODO-140 のきっかけ） | [0, 1, 1, 1] | [0, 1, 1, 1] |
| collected-galaxy-screen-3（m5ekpe） | [1, 0, 0, 0] | [1, 0, 0, 0] |
| collected-galaxy-screen-7（t0480x の取り込み後） | [113, 6, 10, 130] | [113, 6, 10, 130] |

## 要修正

### 1. `analyzer/test_corners.py:28-35` — 写真が `samples/` に入るとこのブランチでも落ちる。main とも区別できない

- 問題: テストは `samples/` で `id == "hedmzy"` の組を探す。`recognizer/import_collected.py:251` の `add` は盤の外を黒く塗ってから
  `samples/` に書く（`paint`）。塗った写真では番号の行の外枠が消えるので、直した分岐を通らない。
- 根拠（実測、上の表）: painted の TL は main・このブランチとも 42px で、しきい値 35 を超える。つまり
  ① 自動の取り込みで hedmzy が入った時点で CI の `test` が落ちる（main を壊すのはこの PR ではなく取り込みの PR になる）、
  ② 直しを外しても結果が同じなので、壊すと落ちるテストになっていない。
- docstring の「Skipped until recognizer/import_collected.py has put the photo in samples/」も、上の理由で前提が成り立たない。

### 2. TODO.md「精度は CI の accuracy で確かめる」— accuracy はこの変更を測らない

- 問題: `recognizer/evaluate.py:39` は `*.truth.json` の正解の四隅で読む。CI に四隅の検出（`find_corners`）を測るものは無い
  （`rg -l "find_corners|check_corners" analyzer/ .github` で該当は今回足した test_corners.py だけ）。
  implementer の報告にも「evaluate.py は正解の四隅を使うので四隅の検出を変えても値が動かない」とある。
- なぜ問題か: implementer の懸念（`INNER_IN` を下げて盤の外の線を内側と誤る）を CI で確かめる、という前提が成り立たない。
  確かめるなら `recognizer/check_corners.py`（全サンプル。CLAUDE.md の規約上は利用者に聞いてから）か、画面の写真数枚に絞って測ることになる。
  どちらにするかは管理者の判断。

## 検討

### 3. `recognizer/corners.py:648-661` — 盤の外を走る辺では、通常の差し替えの対象も「点数の上位 2 本」から「近い 2 本」に変わった

- 問題: `for n, ... in enumerate(tried if out else tried[:SWAP_TOP])` の中で、通常の差し替え（`n >= SWAP_TOP or s2 <= s + SWAP_GAIN` で弾く）は
  `n` の小さい順に効く。`out` のときに並びを近い順にしたので、通常の差し替えが見るのは「点数の上位 2 本」（`SWAP_TOP = 2`）でなく
  「今の線に近い 2 本」になった。内側へ移す規則だけでなく、点数で選ぶ規則の意味も変わっている。
- 根拠: コードを読んだもの。コメント・README・implementer 報告のどれにも書かれていない。測った 5 例では差は出ていない。**実害は未確認。**
- 内側へ移したあと（`out = False`）は、残りの候補は `n >= SWAP_TOP` で全部飛ぶので、遠くて点数の高い線はその周では見ない
  （他の辺が動けば次の周で点数順に見直される）。これは main でも同じ構造。

### 4. `INNER_IN` 0.75 → 0.6 と TODO-140 の理由

- TODO-140（`archives/todo/TODO-140. …md`、reviewer・verifier の報告）に 0.75 を選んだ根拠の記述は無く、食い違いは無い。
  TODO-140 のきっかけの t0480x（元の写真）と m5ekpe（galaxy-screen-3）は、上の表のとおり変わらない。
- 盤の外の線を内側と誤る筋: この規則は `here < INNER_OUT`（0.25 未満）の辺にだけ効き、移す先に `s2 > s - OUT_DROP` と `MIN_SCORE` が掛かるのは main と同じ。
  基準を下げ、さらに「最初に通った近い線」を採るので、番号の行の内側の縁や盤の枠の線のように、近くて 6 割ほど似ている線に先に止まる余地は広がった。
  画面以外（本物の盤の写真で、枠を走る辺）で起きるかは測っていない。**実害は未確認**（要修正 2 の測り方で見える）。

### 5. `recognizer/board.py:78` — 版を 0.30.0（機能の変更）にしたが、中身は直し

- CLAUDE.md「バージョン」: 直しは 0.1.0 → 0.1.1、機能の追加や変更は 0.1.0 → 0.2.0。この項目は読み違いの直しで、
  同じ `_swap` の規則を足した TODO-140 は 0.27.0 → 0.27.1 だった。0.29.3 が合う。README の「recognizer 0.30.0」も合わせて変わる。

## 好みの範囲

### 6. `recognizer/README.md:281` — 「60% 以上 … recognizer 0.27.1、TODO-140」

- 60% は 0.30.0（TODO-175）で変えた値なのに、括弧が 0.27.1 のまま。次の行で 0.30.0 に触れているので誤読はしにくいが、
  「似ている割合が 60% 以上（0.30.0 までは 75%）」のように書くと値の出どころが分かる。`corners.py:95` のコメントも TODO-140 だけ。

## 問題なしの観点

- コメント: 近い順にする理由（外枠のすぐ内側が盤の辺、遠い線はチェッカーの上の端のことがある）を「なぜ」で書いている
- 範囲: corners.py の差分は `_swap` の並べ方と `INNER_IN` だけ。`out` の定義を前に移しただけで式は同じ
- 書式・命名: 周りと同じ（ruff format の形）。`_shift` は既存の関数を使っている
- テストの置き場所: recognizer のテストは `analyzer/test_side.py`・`test_exact.py` と同じく analyzer/ に置く形に沿う
- README の手順 6 の記述は、実装（`out` のときだけ近い順、60%）と合う

## 作り込みすぎ

なし（差分 +9 −3。近い順の距離は既存の `_shift` で x = w/2 の高さを比べるだけ）。

---

# 再レビュー（a9ce604・7ff61f2、e9f63df）

## 前回の指摘

| # | 結果 |
|---|---|
| 1 テストが取り込み後に落ちる・main と区別できない | **解消。** `samples/collected-galaxy-screen-9`（塗っていない元の写真）で、このブランチは pass、`corners.py` だけ origin/main に戻すと FAILED（実測。戻したあとは元に戻し、`git status` はきれい） |
| 2 CI の accuracy は四隅の検出を測らない | **解消。** 上のテストが CI の `test` で四隅の検出を守る。`INNER_IN` 0.6 がほかの写真で外の線を内側と誤らないかは、引き続き CI でも測られない（実害は未確認。前回の 4 と同じ） |
| 3 通常の差し替えも近い 2 本を見る | **コメントで明記された**（`corners.py:652-653`）。コメントにある「点数順だと、内側へ移したあとで遠く点数の高いチェッカーの上の端の線を採る」は、測っていないので**未確認** |
| 5 版 | **解消。** 0.29.3、README の手順 6 も 0.29.3 |
| 6 README の 60% の出どころ | **解消。**「60%（0.29.2 までは 75%）」 |

## 新しい差分

### 好みの範囲: `recognizer/README.md:59` — 精度の表の「recognizer 0.30.0、2026-10-20」

- 版を 0.29.3 に戻したのに、集めた写真の行だけ 0.30.0 のまま。0.30.0 という版は存在しない。0.29.3 が合う

### 問題なし

- `samples/collected-galaxy-screen-9`: 塗っていない元の写真（2048x1839）。縮小して見たところ、盤・番号・アプリのロゴ・ピップ数・マウスのカーソルだけで、人の顔・相手の名前は写っていない。
  truth の note は「added by hand」で、自動取り込みでないことが分かる
- 基準の `collected-galaxy-screen-9`（points 23、bar false）は、塗った写真で書いたものだが、元の写真で
  `evaluate.py` を流しても 23/24・bar wrong で同じ（実測）。README の 1152 中 973 もそのまま使える
- `test_corners.py`: 使わなくなった `pytest` の import を消してあり、`_sample` を外してファイルを直接読む形で短くなった。作り込みすぎ: なし

---

# 再レビュー（083f805: 盤の外の辺は内側へ動く線にだけ移す）

要修正: なし。

## 判定の向き（問題なし。コードを読んで確かめた。実測はしていない）

- この規則が効くのは `out = i % 2 == 0 and here < INNER_OUT` の辺だけで、i = 0（上）と i = 2（下）に限られる。
  `_sides` では上下とも `y = c + x k / 200` なので、`mid` と `inward` と候補の値は、どれも x = w//2 での y 座標になる。左右の辺（`x = c + y k / 200`）はここを通らない
- 画像の y は下向きに増える。上の辺（i = 0）は向かいの辺（下、i = 2）の y が大きいので `inward = +1` になり、y が大きい線（下にある線＝内側）だけが通る。
  下の辺はその逆で `-1` になり、y が小さい線（内側）だけが通る。向きは合っている
- 差が 0（今の線と同じ高さ）は `> 0` で落ちる。今の線そのものは here < 0.25 で、もともと INNER_IN を通らないので、main と変わらない
- `inward` は `out` のときだけ作られるが、条件式は `out and ...` の順で短絡するので、`out` が False の辺で前の辺の `inward` を読むことはない。
  内側へ移した直後に `out = False` になるので、そのあとの候補もこの規則を通らない
- `mid`・`inward`・候補で `_shift(w // 2, int(k))` を同じ形で使っており、比べ方は揃っている

## 検討

### 1. コミットの説明と実装の食い違い: 外側の線は「main と同じ点数順の規則」には戻っていない

- 管理者の依頼文とコミットの本文は「外側の線は main と同じ点数順の規則に任せる」。
  実装では `out` の辺の `tried` は近い順に並んだままで、通常の差し替え（`n >= SWAP_TOP` で弾く）が見るのは
  「近い 2 本」（内側・外側を問わない）。main の「点数の上位 2 本」とは違う。
- 根拠: `recognizer/corners.py:659-663`（並べ方）と `:690-693`（`n >= SWAP_TOP`）を読んだもの。
  コード中のコメント（`:653-654` の「the other swaps then look at the nearest two」）は実装どおりで、食い違うのは説明の側だけ。
  前回の検討 3 と同じ筋。**実害は未確認**（red-brown の悪化がこれで消えるかは verifier の測りで見える）

### 2. `recognizer/README.md:281-282` — 「内側へ動く線だけ」が書かれていない

- 手順 6 は「似ている割合が 60% 以上の線へ … 移す」「今の線に近い順に試す」までで、向かいの辺の方向に動く線に限ることが無い。
  この直しで足した条件なので、1 句足すと実装と合う（例:「向かいの辺の方へ動く線のうち、今の線に近い順に試す」）。
  `docs/corners.md` は `_swap` のこの規則に触れていない（`rg -n "INNER_IN|内側へ" docs/corners.md` で該当なし）

### 3. `recognizer/corners.py:655-660` — 内側かを画像の横の中央 1 点で決めている

- `mid` と候補の高さを x = w//2（画像の中央。盤の中央ではない）だけで比べる。傾きの違う線が盤の幅の中で交差すると、
  中央では内側でも片端では外側、ということがありうる。上下の辺はほぼ水平で、前からある `mid` の比べ方と同じなので、
  起きにくいと見ている。**実害は未確認**

## 好みの範囲

- `corners.py:656` のコメント「a line further out is not "inside it"」は、何に対する inside か（盤の内側）が読み取りにくい。
  「a line moving away from the side across is not a move inside」のように書くと分かりやすい

## 範囲

- `archives/agents/TODO-175/measure.py` に `IN` の環境変数で `INNER_IN` を上書きする行と 2 枚が足されている。測る道具で、アプリの動きは変わらない。問題なし

## 作り込みすぎ

なし（条件 1 つと、向きを求める式 1 つ。既存の `_shift` を使っている）。
