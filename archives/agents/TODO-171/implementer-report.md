# TODO-171 implementer の報告

## 変更点

- `recognizer/board.py`（0.28.0 → 0.29.0）
  - `:103` `pips()`（両者のピップ数の合計）、`:110` `guess_bottom(runs, bar, home, default=1)` を足した
  - `:357` `_finish` で `bottom_colour == "auto"` なら、home の推測より**先に**色を決める。`info` に `bottom_colour`（決めた色）と `colour_guess`（`{"pips": [色 0 を手前にした値, 色 1 を手前にした値]}`、auto でなければ null）を足した
  - `:434` CLI の `--bottom-colour` に `auto` を足した
- `analyzer/app.py`（0.92.1 → 0.93.0）
  - `:265` `/analyze-photo` の `bottom_colour` を `"0"`・`"1"`・`"auto"` の文字列で受ける（既定 `"0"` は今のまま）。ほかは 422（`:312`）
  - `:336` 解析の白・黒の呼び方に、推測した色を使う。`:451-452` 応答に `bottom_colour` と `colour_guess` を足した
- `analyzer/static/app.js`（`APP_VERSION` 0.93.0）
  - `:55` `colourPick` を足した（`homePick` と同じ形）。新しい写真は `"auto"`、PIP をタップして入れ替えたら `"0"`/`"1"`（`:357`）、写真の履歴にも残す（`:512`）。0.93.0 より前の履歴は、覚えていた `bottomColour` をそのまま使う（`:686`）
  - `:991` 写真を読むときに `colourPick` を送り、`:1029` 応答の `bottom_colour` を `bottomColour` にする
  - 端末に覚える色（`keep("bottomColour")`）は、タップしたときだけ書く今のまま。写真なしで盤面を入れるときに使われる
- `analyzer/test_api.py:476` `test_bottom_colour_is_guessed_from_the_pips`（samples の正解を色 2 通りで戻せるか、同点で default）。`:511` `test_api_guesses_home_side` を `bottom_colour=auto` にして、推測した色が正解と同じかを足した
- `analyzer/test_pwa.py:1108` `test_photo_colour_is_guessed_unless_picked`（新しい写真は auto を送って推測を使う、履歴の写真は覚えた色を送る）。`:1010` 送った値を見るため、テストの `FormData` を記録するようにした
- `TODO.md` の TODO-171 の節を、決まったことに合わせて書き直した（「実装する」にチェック、`- [ ] ローカル:` は残した）
- `archives/agents/TODO-171/check_guess.py` 一致件数を数えるスクリプト

## 色と home のどちらを先に決めるか

**色を先に決める。** home の推測（`home_prior`）は色によって答えが変わり、ピップ数は home によって変わるため、どちらかを先にする必要がある。
正解の盤面を、色 2 通り × home 2 通りに入れ替えた 564 通り（141 組）で、正解に戻る数を比べた（`check_guess.py` と scratchpad での試し）。

| 順 | 正解に戻った数 / 564 |
|---|---|
| home を正解のままにして色だけ（指示にあった 141/141 の条件） | 564 |
| 色を home=right のピップ数で決め、その色で home_prior | 449 |
| 色ごとに home_prior で home を決め、その home でピップ数を比べる | 538 |
| **色ごとに左右の少ない方のピップ数で比べ、その色で home_prior（採用）** | **538** |
| 上の採用案を、決めた色・home で何回か繰り返す | 421 |

採用した順は、home が `auto` のとき、色ごとに左右のうちピップ数の少ない方を取り、小さい方の色を手前にする。そのあと、その色で `home_prior` が home を決める（home の推測そのものは変えていない）。
home を `left`/`right` で送ったとき（PWA で置き場をタップしたあと）は、その側だけでピップ数を比べる。samples/external の 8 組も入れた 149 組 × 4 = 596 通りでは 570。

## 同点の扱い

色 2 通りのピップ数が同じなら、色 1（明るい方が手前。PWA の既定と同じ）にする。`colour_guess.pips` の 2 つが同じ値なので、同点だったことは応答から分かる。
564 通りのうち 20 通り（5 組）が同点。同点の代わりに `home_prior` の確からしさで決める案は 540 で、2 通りしか増えないので採らなかった。PWA に同点を知らせる表示（home の「決められず」の文のようなもの）は作っていない。

## 検証

- `uv run ruff check` → All checks passed!（終了コード 0）
- `uv run ruff format --check` → 57 files already formatted（0）
- `uv run pytest analyzer/test_api.py analyzer/test_pwa.py -q` → 89 passed, 1 failed。落ちたのは `test_version_reports_both_parts_and_commit` で、worktree では `.git` がファイルなので `git_commit()` が None を返すため（変更とは関係なく、変更前から worktree では落ちる）
- 壊すと落ちるか: `guess_bottom` の大小を逆にすると test_api の 2 件が落ちた。app.js で応答の色を使わない・`bottomColour` を送るように戻すと test_pwa の 1 件が落ちた（どちらも戻して通ることを確かめた）
- 精度の基準: `evaluate.py`・`check_accuracy.py` は正解の `bottom_colour`（整数）を渡すので、読み取りの結果は変わらない。基準の書き直しは入れていない

## 判断が要る点・残る懸念

- **指示の「141/141 組が一致」は home を正解にしたときの数で、home も推測すると 564 通り中 538（95%）。** 外れる 26 通りは 9 組。うち 3 組（collected-blue-felt-oblique、collected-cream-far、user-1792195518366-wcfrvo）は、色も home も逆にした読みのほうがピップ数が少なくなる。5 組は同点。1 組（user-1792248218172-kuetnz）は `home_prior` が正しい色でも外れる
- 文書は触っていない。`recognizer/README.md:9,16`（`--bottom-colour` は 0/1 だけで「端末に覚えた色を渡す」と書いてある）と `analyzer/README.md:251,263`（`/analyze-photo` の `bottom_colour` と応答の形）が古くなる。直すかは管理者の判断
- 応答の `bottom_colour` は、recognize を差し替えたテストのように `info` に色が無いと、送った値（`"auto"` もありうる）をそのまま返す。本物の recognize は必ず入れる
