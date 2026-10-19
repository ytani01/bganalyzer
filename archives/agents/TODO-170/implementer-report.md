# TODO-170 implementer の報告

## 変更
- 正解ファイルの向きを直した（点検の報告の表どおり）。向きを変えるときは、色の入れ替え＝`points` の符号反転・`bar_white`/`bar_black` と `off_white`/`off_black` の入れ替え・`bottom_colour` の反転、home の入れ替え＝`points` を行の中で左右反転（ポイント p → 13−p（1〜12）、37−p（13〜24））と `home` の反転。`read`（`points`・bar）と `fixed_points` にも同じ変換をした。`cube.at` は盤の物理的な側（手前/奥）なので変えない。
  - samples/（git に入る）: `collected-grey-red-top`（色）、`collected-tan-black-side-1`（色）、`collected-cork-green-side`（色と home）、`photo-orange-black-oblique`（色と home）
  - collected/（git に入らない。`~/work/bganalyzer/collected/`）: `user-1792130519864-ajxlol`（色）、`user-1792243400742-p1vm5a`（色）、`user-1792161634938-n8fzpw`（色と home）、`user-1792179058872-xlkxee`（色と home）、`user-1792407219093-7qrh2u`（home）
- note を書き直した: `photo-orange-black-oblique`・`user-…n8fzpw`・`user-…xlkxee`（手前は灰色、home=left）、`collected-cork-green-side`（手前は緑、home=left。以前の「home を right に直した」は誤りだったと明記）。
- `recognizer/accuracy_baseline.json` を `check_accuracy.py --update` で書き直した（差は `photo-orange-black-oblique` の `home` が True → False の 1 か所だけ。home を left に直したので、アプリの home の推測（right と出す）と合わなくなった。点検済みで、TODO-171 の対象）。
- `TODO.md` の TODO-170 の 4 項目にチェックを入れた。
- `archives/agents/TODO-170/check_pips.py` を足した（向きとピップ数の合計の一致を数える）。
- recognizer のコードは変えていない。版は上げていない。

## 一致件数（samples 95 組 + collected 46 組 = 141 組。TODO.md の「140 組」と 1 組ずれる。collected 側の数え方の違いだと思う）
`uv run python archives/agents/TODO-170/check_pips.py samples/*.truth.json ~/work/bganalyzer/collected/*.truth.json`
- **色だけ 2 通り**（手前の色の推測。直す前に 131/140 だった方）: **141 / 141**（直す前は 132 / 141 で、不一致は直した 9 組）
- **色 × home の 4 通り**で、合計が最小の向きが正解と一致: **126 / 141**（直す前は 117）。9 組は解消。残り 15 組は今回の範囲外
  - 同点（正解と色・home 両方を入れ替えた向きが同じ合計）: collected-red-blue-far、commons-case-dice、dplmij、r0woj7、z0r1g8 の 5 組
  - home を入れ替えた向きの方が少ない: collected-galaxy-screen-2/4/6、we6czo、oq27ns、kuetnz、tecn7k の 7 組
  - 色と home を入れ替えた向きの方が少ない（差 17〜48）: collected-blue-felt-oblique、collected-cream-far、wcfrvo の 3 組
  ピップ数だけで home まで決める推測は、これらでは外れる。正解が誤りとは限らない（実害は未確認。写真は見ていない）。

## 検証
- `uv run python recognizer/check_accuracy.py --update`: 成功（終了コード 0、1568/1800 points）
- `uv run ruff check`: 通過、`uv run ruff format --check`: 通過
- テスト全体は流していない（CI に任せる決まり）

## 判断が要る点・懸念
- TODO-171 の見込み「4 通りの最小が 140 組すべてで一致」は成り立たない（上の 126/141）。home まで推測するなら、残り 15 組の扱い（同点の決め方、home の推測に別の手がかりを使うか）を TODO-171 の着手時に決める必要がある。
- collected/ の 5 組は git に入らない。PR には samples/ の 4 組だけが入る。
