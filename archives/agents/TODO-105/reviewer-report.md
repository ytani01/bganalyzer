# TODO-105 reviewer の報告

対象: ブランチ `claude/todo-105-outline` の未コミットの差分（`git diff`）。
測ったときのスクリプトは scratchpad に置いた使い捨て（`_structure` の新旧比較、退化した四角形、`_along` の向き、固定した隅・crop での `_swap`、keep と `_inner` を外したときにテストが落ちるか）。

要修正: 0 件 / 検討: 5 件 / 好みの範囲: 2 件

## 検討

### 1. `recognizer/README.md:312` collected-m5ekpe の値が測定と合わない

- 内容: 「collected-m5ekpe 9.3% → 0.4%」とあるが、`full-new.json` では 0.00269（0.3%）。
- 根拠: `full-main.json` 0.0931、`full-new.json` 0.002692639781047312（元の大きさ・`--app` とも）。

### 2. `recognizer/README.md:315` 「67 枚の合計で 72.4 秒 → 66.4 秒」は 134 回分

- 内容: `full_corners.py` は 67 枚それぞれを元の大きさと `--app` の 2 回測っており、`seconds` はその 134 回の合計。「67 枚の合計」と書くと 1 回ずつの時間に読める。
  同じ節の photo2 は「3.1% → 1.6%」とだけ書いているが、`--app` は 3.3% のままで変わっていない（photo4 は `--app` を書き分けている）。
- 根拠: `archives/agents/TODO-105/full_corners.py` のループ、`full-*.json` の `photo2.truth.json app` が新旧とも 0.03259。

### 3. `recognizer/corners.py:1-24` モジュールの docstring が手順 4 までのまま

- 内容: 「4. ... the best of all wins.」で終わっていて、縁に沿う割合を点数に足すことと、5 番目の辺の差し替え（`_swap`）が書かれていない。
  docs/corners.md・README は手順 6 まで直してある。
- 根拠: 差分は docstring に触れていない（`sed -n 1,25p recognizer/corners.py`）。

### 4. `recognizer/corners.py:392,408,445,451` 点数の式が 4 か所に書かれている／縦横比と大きさの確かめが guess と `_swap` で 2 か所

- 内容: `_structure(v) + W_ALONG * _along(gx, gy, q)` が 4 回、`wid`・`hgt`・`ASPECT`・`least` の確かめが guess（378-381 行）と `_swap`（439-442 行）に書かれている。
  片方だけ直すと、guess で選ぶ点数と差し替えで比べる点数が食い違う（対で保守するもの）。
  また大きさの確かめは揃っていない: guess は高さを「奥と手前の直線の、写真の真ん中での縦の差」（`yb - yt < least[1] * h`、pin の前）で見ており、`_swap` は「左右の辺の長さの平均」（`hgt < least[1] * h`）で見る。斜めの辺では辺の長さの方が長いので、`_swap` の方がわずかに緩い。
- 根拠: コードを読んだ。実害は未確認（サンプルでこの差で結果が変わるかは測っていない）。

### 5. `recognizer/side.py:159-169`（差分の外）`find_corners_any` の判定は `_structure` だけで見る

- 内容: 普通のモードは、縁に沿う割合を足した点数で四角形を選ぶようになったが、`find_corners_any` は選ばれた四角形の `_structure` だけを `WEAK`（0.7）と比べて、横からの探し方も試すかを決める。
  縁に沿う割合で `_structure` の低い四角形が選ばれると、今までより多く横からの探し方に回る（時間が増える、横からの方が勝つ）ことがありうる。
  README（668-672 行）・docs/corners.md の「縁に沿う割合は足さない」の記述そのものはコードと合っている。
- 根拠: `side.py:_score` は `C._structure(v)` だけ。実害は未確認（main と新しい版で `find_corners_any` の `side` が変わる写真があるかは測っていない）。

## 好みの範囲

### 6. `recognizer/corners.py:452-454` `_inner(v2, i)` を 2 回計算している

- 条件の `_inner(v2, i)` と、採ったあとの `here = _inner(view, i)`（`view` は `v2`）は同じ値。1 回だけ計算して変数に入れれば足りる。

### 7. `recognizer/corners.py:428,457-458` `before` と `break` は無くても同じ結果

- ある周で 1 本も動かなければ、keep 以外の辺はすべて `looked[i] == moves` になり、次の周では全部飛ばされる。`before` と `if moves == before: break` は空の周を省くだけで、結果は変わらない（読み手には早く抜ける意図が分かりやすいので、残してもよい）。

## 作り込みすぎ

- `corners.py:L452-454: shrink: _inner(v2, i) を条件と代入で 2 回。inn = _inner(v2, i) を 1 回、here = inn.`
- `corners.py:L428,L457-458: delete: before と break。looked/moves で空の周は何もしない。`
- `corners.py:L392,408,445,451: shrink: 点数の式 4 回。_score(view, gx, gy, q) 1 つにまとめる（行数はほぼ同じ、式が 1 か所になる）。`
- `corners.py:L378-381,L439-442: shrink: 縦横比と大きさの確かめ 2 回。_fits(q, w, h, least) 1 つ（guess と高さの測り方を揃えるなら）。`

net: -4 lines possible.

## 問題が無かった観点（1 行ずつ）

- `_swap` の keep: 辺 i は隅 i と (i+1)%4 をつなぐ（上=0-1、右=1-2、下=2-3、左=3-0）ので、`i in keep or (i + 1) % 4 in keep` は正しい。固定した隅は `_corners` で計算し直されるが、ずれは 1.4e-14〜2.8e-14 px で、`exact.snap(q, 0.1)` 後は元の値と一致した（screen1・photo4・travel-case・m5ekpe ほか 8 枚 × 固定 3 通り。全部 fixed kept: True）。
- keep の確かめを外すと `test_corners_keep_the_fixed_ones_and_look_in_the_trimmed_part`（screen1、TL・TR 固定）が落ちる（TL が 286 → 290.3）。テストで捕まえられている。
- `_inner` の歯止めを外す（`INNER_SLACK = 10`）と `test_corners_are_found_on_samples` の commons-dark-homeleft（3.61%）と photo6（5.89%）が落ちる。テストで捕まえられている。
- `looked`/`moves` で飛ばすのは「前に見てから、どの辺も動いていない」ときだけで、そのとき候補の四角形（ほかの 3 辺 + 候補の直線）は前と同じ。辺 i 自身が動いた直後も、ほかの 3 辺は同じなので候補は同じ。比べる相手の `s`・`here` は変わっているが、上位 2 本の評価は同じ結果になる（1 本目が `_inner` で落ち 2 本目が採られた場合だけ、`here` が下がって 1 本目が通りうる。その場合は飛ばすことで差し替えの連鎖を防ぐ側に働く。実害は未確認）。
- `least`・`ASPECT` の確かめ: 縦横比は guess と同じ式・同じ範囲。大きさは上の 4. のとおりわずかに違う。
- crop: 8 枚で crop を付けて走らせ、`_swap` の結果が `small` の範囲（0〜w, 0〜h）の外に出たものは無かった。guess も範囲の確かめはしておらず、`_swap` だけが外へ出る作りではない。ただし `_swap` は左右の直線を、見つけたのとは別の奥・手前の組と組み合わせるので、guess より遠くまで延びた交点を作りうる（試したサンプルでは起きていない）。
- `_sides`/`_corners` のゼロ割り: 上の辺が垂直・右の辺が長さ 0 の四角形では、`np.float64` 同士の割り算なので例外にならず inf/nan と RuntimeWarning になり、`_swap` の `ASPECT` の確かめ（nan との比較は偽）で飛ばされる。guess を通った四角形（縦横比と NEAR の確かめ済み）でこの形になる道は見当たらない。
- `_meet` の分母: 候補の直線どうし（傾きは ±100/200）では `1 - kh*kv/40000 >= 0.75`。`_sides` から来る直線と組むときは `np.float64` なので 0 でも例外にならない。
- `_along` の向き: `np.roll(a, -1) - a` は上・右・下・左の順、`upright` は 1・3（右・左）で gx、上下は gy。合成画像で、横の縁だけの画像 0.5、縦の縁だけの画像 0.5、長方形 0.85（頭打ち）、画像の外の四角形 0.0 で、取り違えは無い。
- `_structure` の書き換え: 新旧の実装を 450 個の view（実写 4 枚の四隅をずらした 104×80 と 208×160 の 400 個、乱数の画像 50 個）で比べ、値が違ったものは 0 個。`d` は「int32 − 0.5 刻みの中央値」なので 2 乗は 0.25 刻みで、和は足す順によらず正確。
- `_point_templates` の返り値の形の変更: `_TEMPLATES`・`_point_templates` を使うのは `corners.py` の中だけ（`rg -n '_TEMPLATES|_point_templates|_structure' recognizer analyzer tools`）。`side.py` は `_structure` を呼ぶだけで影響なし。
- `docs/corners.md` の数字（40 点、2 px、0.85、0.4、6 本、104×80・208×160、上位 2 本、最大 3 周、0〜3% と 6〜12%、24 区間、0.1）はコードの定数と一致。横からのモードで縁に沿う割合も差し替えも使わないという記述も、`side.py` が独自の `_guess` と `_structure` だけを使うことと一致。
- README の 77 → 90、45 → 32、見つからない 12、ずれが増えた 8 枚（0.1〜3.2%）、72.4 → 66.4 は `full-*.json` から再計算して一致（2. の書き方を除く）。
- バージョン: recognizer のアプリのコードを変えたので 0.25.0 → 0.26.0（機能の変更で minor）は CLAUDE.md の決まりどおり。analyzer は変わっていない。
- 範囲: 差分は corners.py・テスト・文書・版・TODO.md だけで、指示に無い変更は無い。
- コメント: 新しい定数・関数のコメントは「なぜ」（頭打ちの理由、歯止めの理由、einsum が正確な理由）を書いている。行の長さは既存（最大 145）の範囲。
