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
