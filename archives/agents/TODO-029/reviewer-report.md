# TODO-029 reviewer 報告（recognizer 0.6.2、MAX_MARKS 4 → 8）

対象: `git diff main...HEAD -- recognizer`（claude/cube-marks-pi、7d621f4）。関連して TODO.md と docs/PI_CHECKS.md も見た。

## 実測

この Raspberry Pi（aarch64、OpenCV 5.0.0・numpy 2.5.4。`bganalyzer` コンテナの中も同じ版）で、
`cube._ink` を包んで、`read_cube` に来た候補ごとに `(位置, share, marks)` を記録した。
`found` と `seen` を cube.py と同じ式で上限 4 と 8 の両方について組み直した。対象は 30 枚で、元の写真と、アプリと同じように縮めた写真（`app=True`）の両方。
スクリプトと出力: `/tmp/claude-649/-home-ytani-work-bganalyzer/a4557ce2-6d03-411b-be65-35feab896e1c/scratchpad/marks.py`、`marks.txt`
（セッション用の一時ディレクトリにあるので、残すなら管理者が移す）。

上限 8 にすると、候補の見つかる回数（seen）が変わったもの:

| データ | 上限 4 | 上限 8 | 答え |
|---|---|---|---|
| photo3（元の写真） | 2 回（marks 2,2） | **5 回**（2,2,5,5,5） | None → centre |
| photo3（アプリ） | 5 回 | 5 回 | centre のまま |
| screen2 | 11 回 | 13 回（5,6 が加わる） | black のまま |
| bray-intermediates-105 | 8 回 | 21 回（6 が 13 回） | centre のまま |
| **commons-tavli-red-brown** | 候補なし | **新しい候補が 3 回**（marks 5,5,5） | None のまま |
| commons-travel-case | 候補 1 つ | 新しい候補が 1 回（marks 7） | None のまま |

tavli-red-brown の新しい候補を切り出して見ると、ダイスではなく、ポイントに重なった駒（中央にくぼみのある駒）だった。
travel-case の候補はケースの縁の縫い目。ダイスの 5・6 の面が `_face_value` をすり抜けて入った例は、30 枚の中には無かった。

## 検討

### 1. 本物と偽物の差が、Pi では 5 回対 3 回まで縮んだ（recognizer/cube.py:17、:18）

- 何が: Pi の元の写真で、photo3 のキューブは 5 回見つかり、`MIN_READINGS = 4` を 1 回だけ上回る。
  一方、上限を上げたことで tavli-red-brown の駒が 3 回見つかる候補になり、`MIN_READINGS` に 1 回足りないだけになった。
- なぜ: 0.6.0 で photo3 が「7 回／必要 6 回」のぎりぎりで割れたのと同じ形が、キューブの側と偽物の側の両方に出ている。
  `MIN_READINGS` のコメント「the samples' other squares: 3 at most」と README の「キューブ以外の正方形は多くて 3 回」は、
  今も成り立つ（3 回）。ただし上限 8 で増えたのは、`circles` の判定（`c[2] > 0.47 * side`）をすり抜けた駒だった。
  2 倍の条件は、キューブが写っていない写真の偽物は止めない（候補が 1 つだけになるので）。
- 実害は未確認（30 枚では誤検出なし）。x86_64 で tavli-red-brown が何回になるかは測っていない。

### 2. ダイスの 5・6 を止める二つ目の条件が無くなった（recognizer/cube.py:79-82）

- 何が: 0.6.1 までは、ダイスの 5・6 の面が `_face_value` をすり抜けても、`marks <= 4` で落ちていた。上限 8 では、確かでないダイス
  （`dice` の `sure` が偽）の 5・6 の面を止めるのは `_face_value` だけになる。
- なぜ: 目の大きさが面の 3〜4% 程度なら、6 個で `share` が 0.04〜0.4 に入る。commons-case-dice（ダイス 5-3、dice は読めない）では、
  上限 8 でも候補は出なかった。それ以外に、確かでないダイスの 5・6 が写ったサンプルは見当たらない。
- 実害は未確認。サンプルに例が無いので、測れていない。

### 3. docs/PI_CHECKS.md の PI-008 がまだ 0.6.1 のまま（docs/PI_CHECKS.md:63-64、差分に無い）

- 何が: 「recognizer 0.6.1 で直した」「0.6.1 で確かめ直す」とある。しかし Pi の 0.6.1 でも photo3 は `not found` だった
  （`archives/agents/TODO-029/pi-evaluate-0.6.1.txt`）。直したのは 0.6.2 になる。
- なぜ: CLAUDE.md の「マージ後に Pi で確かめる必要がある変更は、その PR の中で docs/PI_CHECKS.md に項目を足す」。
  このままだと、Pi の Claude Code が 0.6.1 で確かめ直して、また失敗と書く。TODO.md:69 の「Pi で PI-008 を確かめ直し」とも合わせる。
- 重大度は**要修正**寄り。この PR で直す必要があるかは管理者が判断する（文書だけで、recognizer の差分の外なので、ここに置いた）。

### 4. README の「当たり具合」の photo3 の行が、Pi の 0.6.2 と合わない（recognizer/README.md:237、:241）

- 何が: 237 行は「0.6.2 は Raspberry Pi で測って同じ」。241 行の photo3 は「7 回見つかる。JPEG で保存し直すと 4〜5 回」で、
  これは x86_64・0.6.1 の数。Pi・0.6.2 では元の写真で 5 回（marks 5 の 3 回を含む）。
  TODO.md:70 の「塊は 8 段階で見つかっている」とも数が違う。こちらは `_ink` の前の数かもしれない（未確認）。
- 0.6.2 を x86_64 で測っていないことも、表からは読み取れない。上限 8 は x86_64 の見つかる回数も変えうる。
  たとえば photo3 で、割れた印が x86_64 でも 5 個以上になる段階があれば回数が増える（未確認）。

### 5. README の手順 5 の括弧書きが、原因を取り違えて読める（recognizer/README.md:233）

- 何が: 「0.6.0 までは 6 回。photo3 が Pi で見つからなかった」とある。これだと、回数を下げたことで Pi が直ったように読める。
  実際は、Pi では 0.6.1（必要 4 回）でも見つからず（元の写真で 2 回）、0.6.2 で 5 回になって見つかった。
  手順 4 の括弧書きが本当の原因になる。cube.py:98 のコメント「on the Raspberry Pi fewer: 6 was too many to ask」も同じように読める。
- 1 文足すかどうかの問題で、好みの範囲に近い。

## 好みの範囲

- recognizer/board.py:39 のコメント「The recognizer's version (board.py, position.py, corners.py and dice.py)」に cube.py が無い。
  TODO-025 からあり、この差分で入ったものではない。

## 範囲外で気づいたこと（報告だけ）

- `samples/external/` の bray 7 枚の `*.truth.json` には `cube` が無い。しかし盤面図にはキューブが描かれている（bray-beginners-107 は中央に 64）。
  このため evaluate.py は、そのうち 6 枚を `cube WRONG (read centre/white/black, truth None)` と出す。上限 4 でも 8 でも同じで、
  この差分とは関係しない。「全 30 枚で誤検出なし」を数えるときは、この 6 枚を除いているはず（README の「キューブのない 17 枚」は外部の 7 枚を含まない）。
  正解を付けるかは別の項目になる。

## 問題なし

- 版上げ: recognizer 0.6.1 → 0.6.2 は直しの上げ方に合う。analyzer は変えていないので `APP_VERSION` は要らない。
- `MAX_MARKS` の置き場所と命名は、ほかの定数（`MIN_READINGS` など）と揃っていて、コメントに理由がある。
- README 手順 4 の「1〜8 個」は `MAX_MARKS = 8` と合っている。
- テスト: recognizer にはテストが無く、evaluate.py で確かめる決まり（CLAUDE.md「精度の確認」）。足りないものは無い。
- 範囲: 指示に無い変更は無い。
- 作り込みすぎ: なし（Lean already. Ship.）
