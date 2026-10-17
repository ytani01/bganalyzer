# TODO-101 確認報告（verifier）

対象: `claude/photo5-home-right` の未コミット差分。コードは変更していない。

## 結果の要約

確認した 5 項目はすべて指示どおり。食い違いは無し。
ただし `samples/photo5.truth.json` の `note` 欄も変わっている（指示に明示は無いが、同じファイル内の変更）。下の 2 を参照。

## 1. points が旧 points の鏡か（一致）

- `recognizer/home_prior.py` の `mirror` を `git show HEAD:samples/photo5.truth.json` の points に当てた結果と、新しい points は完全に一致した（`mirror(old) == new: True`）。
- 逆向きの `mirror(new) == old: True` も一致。
- 駒数: 旧 white 15 / black 15、新 white 15 / black 15。

## 2. home と points 以外の変更（一致。note のみ例外）

`git diff` で変わったのは `samples/photo5.truth.json` の 2 行（ファイル全体は 2 行のみ）。内容を比較した結果:

- 同じ: `corners_TL_TR_BR_BL`、`bottom_colour`（1）、`dice`（[6,2]）、`cube`（{"at":"centre"}）、`bar_white`・`bar_black`・`off_white`・`off_black`（すべて 0）、`image`。
- 変わったのは `home`（left → right）、`points`（鏡の値）、`note`。

`note` には「TODO-101: home on the right (was left by mistake).」が追記されている。
これは指示の列挙には無い変更だが、truth の注記で、判定には影響しない。
「was left by mistake」は作業メモの言い回しで、写真を見て決めた事実かどうかは私の側では確かめていない（判断できない）。

## 3. evaluate.py（一致）

```
$ uv run python recognizer/evaluate.py samples/photo5.truth.json
photo5.truth.json: 24/24 points correct, bar ok, home guess ok (+16.5), dice not read (read None, truth [6, 2]), cube ok (read None, truth centre)
exit=0
```

24/24 と `home guess ok` を確認した。

## 4. accuracy_baseline.json の photo5 行（一致）

```
52: "photo5": {"points": 24, "bar": true, "home": true, "dice": "not read", "cube": "ok"},
```

指示の期待値（points 24, bar true, home true, dice "not read", cube "ok"）と一致。
差分は `home` の false → true の 1 か所のみ。

## 5. テスト（両方 通過）

- `uv run pytest -q analyzer/test_api.py -k home_side_is_guessed`: `1 passed, 48 deselected`、exit=0
- `uv run pytest -q analyzer/test_side.py`: `15 passed`、exit=0

`test_api.py` の差分は photo5 の例外（`continue`）と、その説明コメントの削除のみ。

## 確かめられなかったこと・判断が要る点

- 「photo5 の正解は home right」が写真と合っているかは確かめていない。TODO.md にある「2026-10-18 ユーザーが写真を見て決めた」という記述を前提にしている。
- テストが「例外を外したことで、外れる局面を見逃す」壊れ方をするかは確かめていない（指示の範囲外。`home_prior.guess` を壊す確認はしていない）。
- `analyzer/test_api.py` の変更は、この 1 ファイルの 1 テストを見ただけで、全体のテスト（CI の test）は流していない（指示どおり）。
- 全サンプルの精度（`check_accuracy.py`）も流していない（指示どおり）。
- 境界線上の判断: 無し。実害は未確認の項目も無し。
