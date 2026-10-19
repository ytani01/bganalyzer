# TODO-160 implementer 報告

## 変更点
- `analyzer/static/board-view.js:260-270`（`drawCube`）: ダブルされたところのキューブの横を `fieldCx(cube.at)`（ダブルされた人）から、`fieldCx(ダブルした人)` に変えた。縦（`cube.at` の側の半分、真ん中から ±75.25）はそのまま。コメントも直した。
  - 手前がダブル（`cube.at = black`）→ 右の場の奥寄り、奥がダブル（`cube.at = white`）→ 左の場の手前寄り。
- `analyzer/README.md:81`: キューブの場所の説明を直した。
- 版: analyzer 0.88.2 → 0.88.3（`analyzer/app.py:33`、`analyzer/static/app.js:14`）。
- `TODO.md`: TODO-160 のチェック 2 つ（位置、版）を入れた。`ローカル:` の行は未チェック。

## 自分で確かめたこと
- `uv run pytest analyzer/test_pwa.py -q`: 32 passed。
- 位置は式だけで、画像では見ていない（確認は verifier）。位置を見るテストは元から無い（ブラウザが要る）。

## 残る懸念
- 画面での重なり（ダイス位置は出ないので問題ないはず、矢印・チェッカー）は未確認。
- 並行の TODO-159（PR #473）が `TODO.md` を変えるなら、先頭の「残っている項目」の行などでぶつかるかもしれない。

## 追記: 重なりを避ける横位置（main の指示 2026-10-20）
- `analyzer/static/board-view.js`: `offeredCubeCentre(b, home, at)` を足し、`drawCube` が使う（`drawCube` に盤面 `b` を渡す）。
  縦は今のまま。横は、ダブルした人の場の真ん中から 24 ずつ（ポイントの上・ポイントの間）、真ん中に近い順（0, -1, +1, -2, …, ±5）に、
  キューブの四角（縁 2.5 含む）と積まれたチェッカー（最大 5 個、縁含む）の円が重ならない最初の位置を選ぶ。どこも重なるなら真ん中（今の位置）。
  バーのチェッカーは場の外なので見ない。テストから呼べるよう `module.exports` と戻り値の `offeredCubeCentre` を足した。
- テスト `analyzer/test_pwa.py` 末尾 `test_offered_cube_keeps_clear_of_checkers`: 空の盤で真ん中（手前・奥の 2 通り）、重なる局面で 24 ずれる（2 通り、縦は変わらない）、
  重ならない局面（チェッカー 1 個）で真ん中、全部のポイントに 5 個で真ん中。
- 壊すと落ちるか: 重なり判定を常に真／常に偽にすると落ちた（2 通りとも確認）。判定のすきまの閾値を `B.r - 6` に緩めても落ちない（境界の値は見ていない）。
- 版: origin/main の 0.89.0（TODO-159）の次の 0.89.1（`analyzer/app.py`・`analyzer/static/app.js`）。main をマージして `README.md`・`app.py`・`app.js` のぶつかりを解いた
  （README は main 側の文に TODO-160 の説明を足し直した）。`TODO.md` の先頭の行はぶつからなかった。
- 検証: `uv run pytest analyzer/test_pwa.py analyzer/test_photo_view.py -q` → 46 passed。画面での見え方は未確認（verifier）。

## 追記: レビューの検討の反映
- 候補を `[0, 1, -1, 3, -3, 5, -5]`（24 ずつ）にし、ポイントの間（偶数）を消した。同じ距離ならバー寄りを先に見る（どちらの場でも。`toBar`）。
- テストに、21・22 の両方に 3 段ある局面（右の場、バー寄りの 420）と、その鏡（左の場、236）を足した。バー寄りの向きを固定する・±3 の順を逆にするのどちらでも落ちることを確かめた（±1 の順だけ逆にしても落ちない。柱が両方をふさぐため）。
- README の説明を、ふだんは場の真ん中、重なるときだけポイントの上へずらす順に直した。TODO の節の見込みにレビューを入れ、決定を書き足した。
- `uv run pytest analyzer/test_pwa.py -q` → 34 passed。
