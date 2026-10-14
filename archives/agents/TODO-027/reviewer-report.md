# TODO-027 reviewer の報告

対象: `git diff origin/main...HEAD`（ブランチ `claude/todo-027-dark-checkers-impl`、324115f まで）。
`recognizer/board.py` を中心に、`recognizer/README.md`、`docs/PI_CHECKS.md` も見た。
実測は Pi（aarch64）で `uv run -q --no-project --python 3.12 --with opencv-python-headless --with numpy` を使った。
使ったスクリプトは scratchpad に置いた（残していない）。

## 要修正

### 1. `recognizer/board.py:770` 同じ円が 2 つあると `ValueError` で落ちる

- **何が問題か:** `rest = [s for s in rest if s not in more]` の `in` はタプルを `==` で比べる。
  5 番目の要素 `med / LAB_W` が numpy の配列なので、x・y・r・score が同じで別のオブジェクトのタプルどうしを比べると
  `ValueError: The truth value of an array ... is ambiguous` になる。
- **起きる条件:** 同じ円（x, y, r が完全に同じ）が `scored` に 2 つあり、両方が "shown" の位置にあって、
  両方とも同じ回の `more` に入るとき。score は x, y, r だけで決まるので 2 つは同じ値になる。
- **根拠（実測）:**
  - 同じ円は実際に出る。Hough を 3 つのチャンネル（gray、a、b）で回した結果を縦に積んでおり、重複を除いていない。
    23 枚のうち 16 枚で、1 回の `detect_checkers` に完全に同じ (x, y, r) が 1〜10 組あった（screen1 は 10 組、tavli-red-diamond は 4〜5 組）。
  - Hough の結果を 2 回ずつ返すようにして `recognize` を動かすと、commons-rollup-oblique と commons-dark-homeleft が
    board.py:770 で `ValueError` になった（case-midgame、photo2、photo4、leather-cups は通った）。つまりこの 2 枚では救い出す処理が実際に働いており、
    そこに同じ円が重なれば落ちる。
  - 公開サンプル 23 枚をそのまま動かした範囲では落ちなかった（重複が "shown" の位置で救い出される組み合わせが無かった）。
    ai1 の盤の写真や利用者の写真で起きるかは**実害は未確認**。起きると `/analyze-photo` が 500 になる。
- 同じ問題は `scored` の要素を比べる書き方を変えない限り残る（直し方は書かない）。

### 2. `recognizer/accuracy_baseline.json`・`recognizer/README.md:93` 精度の基準と表が直っていない

- **何が問題か:** CLAUDE.md「精度の確認」は、認識を変えたら README の「精度」の表を更新し、良くなったときは
  `check_accuracy.py --update` で基準を書き直して**同じ PR に入れる**と決めている。差分ではどちらも変わっておらず、
  `accuracy_baseline.json` の dark-homeleft は 12、README の表（93 行）も 12、72 行の「23 枚で 552 ポイント中 495」も古いまま。
- **起きること:** CI の `accuracy` は下がったときだけ落ちるので、このままでも通る。ただし 22 に上がった分が基準に入らず、
  あとで dark-homeleft が 12 に戻っても CI は気づかない。
- **判断が要る点:** 基準は x86_64 で測る決まり（Pi では更新しない）。この Pi の上では書き直せないので、誰がどこで測るかを決める必要がある。
  依頼では「精度の再測定は別の担当」とあるが、PR に入れる決まりなので、マージ前に入っているかを確かめる必要がある。

## 検討

### 3. `recognizer/board.py:646-649`、`:823-825` 深さ 4 の位置が盤の真ん中を越えうる

- **何が問題か:** 深さ k の位置は `pitch * (k + 0.5)`。k = 4 で 4.5 × pitch が `lay.h / 2`（500）を越えると、
  "top" の深さ 4 が下半分に入る。`add_hidden_stacks` がそこに足した駒は `count_from_circles` では "bottom" の列に振られる。
- **起きる条件:** pitch > 111。pitch は `2 * median(r)` で測り直され、上限は Hough の maxRadius から pw の約 1.26 倍。
  aspect が大きい盤（a の上限 648 → pw 108 → pitch 136）では届く。
- **実測:** 23 枚の最後の pitch は 71.7〜105.3 で、越えたものは無い。**実害は未確認**
  （足した駒は下の列の根元から 2.3 個分より遠いので、下に駒が無ければ数えられず、上の列が 1 個少なくなるだけと読める）。

### 4. `recognizer/board.py:762-764` 「捨てない円が 2 個以上」に、駒にならない弱い円も入る

- **何が問題か:** 数えているのは `scored` のうち "shown" でない円で、score が GAP_MIN_SCORE（0.6）以上なら入る。
  CIRCLE_MIN_SCORE（0.85）に届かず、あとの `clear` と山の間の判定で落ちる円も「山」の 2 個に数える。縦に続くかの判定（`for k in keep`）も同じ。
- **起きる条件:** 空いた三角形の根元に弱い円が 2 個以上出る列。そこに "shown" の円があると救い出される。README の説明
  （「同じ列に捨てない円が 2 個以上あり」）とは食い違っていないが、README が言う「山」より広い。境界線上なので報告だけ。**実害は未確認**。

### 5. `recognizer/board.py:988` 足した駒がダイスとキューブの読み取りを止めうる

- **何が問題か:** 足した円（r = pitch / 2）は `circles` に入り、`dice.read_dice`（dice.py:195-197）と `cube.read_cube`（cube.py:74）が
  「駒の上の四角」として除く。README（141-143 行）は「ダイスやカップが三角形を隠す」ことを "hidden" の誤りとして挙げており、
  円が 1 個以下の列ではそれが駒として足され、そのダイスも読まれなくなる。
- **実測:** 23 枚で駒が足されたのは dark-homeleft（15 個）、rollup-oblique（4 個、x=1159 の上の列）、photo2（3 個、x=618 の上の列）だけ。
  ダイスの結果が変わったかは測っていない（精度の再測定は別の担当）。**実害は未確認**。

### 6. `recognizer/README.md:23-30` 「仕組み」の 4 が古い

- board.py の docstring（Pipeline の 4）は「三角形の辺が見える位置の円を捨てる」「隠れた列に駒を足す」を足したが、
  README の「仕組み」の 4 は前のまま。TODO-027 の節（132-147 行）には書いてあるので、仕組みの側にも 1 行あると食い違わない。

### 7. `recognizer/README.md:172` 「読み取りが 12/24 の dark-homeleft は差が 1.6」

- home guess の節。0.11.0 で 22/24 になったので、差の値も変わっているはず。日付も版も書いていない記述なので、今の値として読まれる。測っていない。

### 8. テスト

- 1 の落ち方は、同じタプルを 2 つ入れた `scored` で救い出しの処理を通すだけで再現する。`column_texture` も含め、
  recognizer の新しい処理には単体のテストが無く、`accuracy` だけが見ている。1 を直すなら、壊すと落ちるテストを 1 本足すか検討。

### 9. `docs/HANDOVER.md:29`

- CLAUDE.md「共同開発」は進み具合を `docs/HANDOVER.md` に書くと決めている。TODO-027 は「再開した」のままで、0.11.0 の結果が無い。
  マージのときに書くつもりなら不要。

## 好みの範囲

- `docs/PI_CHECKS.md:91` 「足した日・PR」に PR 番号（#112）が無い（ひな形は `PR #42（TODO-018）`）。

## 問題が無かった観点

- バージョン: recognizer だけを 0.10.0 → 0.11.0（機能の追加なので minor）。analyzer は変わっていないので `APP_VERSION` も変えなくてよい。
- 深さ 0 の扱い: `add_hidden_stacks` は深さ 1 から続く "hidden" を条件にし、深さ 0 が "shown" なら足さない。README の説明と合っている。
- 円が 1 個以下の数え方: `> 1` で飛ばすので「2 個以上の列には足さない」と合っている。
- `_slot_of` の列の許容 0.3 個分: README 150 行の「0.3 個分より外れた円は辺を確かめていない」と合っている。k < 0 と深さ 5 以上は辺を見ない（`tex.get` が None）。
- `column_texture` の中央値が NaN: 全部の位置が画像の外のときだけで、`not med >= TEX_MIN` で飛ばす。23 枚で RuntimeWarning は出なかった。
  位置は余白 m = 60 の内側に収まる（y − r = m + 0.05 × pitch）。
- `add_hidden_stacks` の切り出し: X − r = m + (pw − pitch) / 2 で、pitch の上限（pw の約 1.26 倍）でも 60 − 13 > 0。はみ出さない
  （はみ出すと NaN ではなく `[inner]` の IndexError になる書き方なので、前提が崩れたら落ちる）。
- `count_from_circles` との整合: 足すのは 1 列に 2 個以上なので LONE_MIN_SCORE（1.0）の「1 個だけの駒」には当たらない。
  x は列の中心なのでバーには入らない。色は detect_checkers と同じ `_top_colour` と `LAB_W` の扱いで、2-means に入る。
- `add_hidden_stacks` の呼ぶ位置: 測り直し・盤の色の学び直し・列の合わせ直しのあと 1 回だけで、コメントで理由を書いている。
- 行長: 足した行で 121 字を超えるものは無い（既存の書き方と同じ）。
- 範囲: recognizer、README、PI_CHECKS、TODO.md 以外の変更は無い。`_top_colour` の切り出しは中身を変えていない。
- PI-022: 「次の番号」「残っている項目」を直し、新しい番号を上に置いている。

## 作り込みすぎ

- `board.py:L805-808`: shrink: `add_hidden_stacks` が Lab のぼかしと Sobel と `column_texture` を detect_checkers とまったく同じ画像・lay・pitch で計算し直している（最後の detect_checkers と同じ結果）。`recognize` の slots の分岐（board.py:991-994）も同じ 3 行。`_lab_gradients(ground)` のような 1 つの関数にまとめるか、最後の detect_checkers の `tex` を渡せば、3〜4 行減る。
- `board.py:L762-768`: shrink: `sum(... for k in scored if not k[5]) >= 2` は `while` の回ごとに変わらない。ループの前に「同じ列に 2 個以上ある "shown" の円」に絞っておけば、`while` の中は縦に続くかだけになる（1 の直しと一緒にやると短くなる）。

net: -4 lines possible.
