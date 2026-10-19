# TODO-171 ローカルの確認（verifier、2026-10-20）

結果: **期待どおり**（手前の色の推測 2/2 一致、home を手で変えたあとの読み直しで色は変わらず）。実害は未確認の点を最後に 1 つ書く。

## 更新

- トップの作業ツリーは main の 33e73e7（`git pull`: Already up to date）。サービスは再起動済み（`systemctl --user status`: active、起動は確認の約 30 秒前）。
- `/version`: `{"analyzer":"0.93.0","recognizer":"0.29.1","commit":"33e73e7",...}` — 一致。画面のヘッダーも `a0.93.0 · r0.29.1 · 33e73e7`。

## 手前の色（localStorage の `bottomColour` を正解と逆にしてから、四隅は truth の値で読ませた）

操作: `tools/live_view.py` のブラウザ（CDP 9222）に Playwright の `connect_over_cdp` でつなぎ、新しいタブで操作。
`localStorage.bottomColour` を設定 → 再読み込み → 写真を入れる → corners を truth の値にする → `#recognize`。
`homePick` と `colourPick` は既定の `auto` のまま（`pi_ui_check.py` の `read_photo` は色を `update` で正解に直してしまうので使わず、別のスクリプトを組んだ。`scratchpad/t171.py`）。
`collect` は `off`（`collected/` を増やさない）。

| 写真 | 正解の bottom_colour | 読む前に覚えさせた値 | 読んだ後の `state.bottomColour` | 名前（手前, 奥） | PIP（手前, 奥） | home（正解 → 結果） |
|---|---|---|---|---|---|---|
| collected-app-green-far（手前が明るい） | 1 | 0 | **1** ✓ | 白, 黒 ✓ | 103, 112 | right → right（`homeGuess.margin` 12.7） |
| collected-app-green-shot（手前が暗い） | 0 | 1 | **0** ✓ | 黒, 白 ✓ | 123, 126 | left → left（`homeGuess.margin` -12.8） |

- 手前の PIP は、正解の盤面から計算した値と一致（far 103、shot 123）。shot の奥は 126 で一致。
- 読んだ後も localStorage の `bottomColour` は逆の値のまま（far "0"、shot "1"）。推測した色は端末に覚えさせていない（PIP をタップしたときだけ `keep` する作りと合っている）。

## 置き場をタップして home を変え、読み直す（shot で実施）

| 段階 | bottomColour | colourPick | homePick / home | PIP |
|---|---|---|---|---|
| 読んだ直後 | 0 | auto | auto / left | 123, 126 |
| 置き場（`rect[height=101]`）をタップ | 0 | "0" | right / right | 168, 165 |
| 「戻る」→ 四隅の画面 → 「盤面を読み取る」（読み直し） | **0**（変わらず） | "0" | right / right | 168, 165 |

- 色は変わらなかった ✓。タップで `colourPick` が "0" に固定され、読み直しはその色で送られている。

## 確かめられなかったこと・実害は未確認の点

- far の奥の PIP は 112 で、正解の盤面から計算した 136 と違う。truth.json の `read` 欄にも `bar_black: 1`（正解は 2）とあり、この組は元から駒の読み違いがある組（今回の項目の範囲外）。読んだ盤面の points は今回取っていないので、この差が既知の読み違いだけで説明できるかは確かめていない。実害は未確認。
- 読み直しのときの `/analyze-photo` のリクエスト本体（`bottom_colour` の値）は取っていない。`colourPick` が "0" になっていたことと、結果が変わらなかったことから見ているだけ。

## 後始末

- ブラウザ（live_view）は開いたまま。操作用に開いたタブも閉じていない。
- コード・設定は変更していない。コミットなし。`collected/` は増やしていない（`collect` を `off` にした）。
