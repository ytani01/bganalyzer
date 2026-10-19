# TODO-170. 向きが逆になっている正解ファイル 9 組を直す

| | main | 担当 |
|---|---|---|
| 見込み | Sonnet 5.5 / effort medium | implementer（Sonnet 5.5）+ verifier（Sonnet 5.5）。挙動は変わらないので reviewer は無し |
| 実施 | Sonnet 5.5 / Opus 5.5（main の記録は混在） | implementer（Sonnet 5.5）+ verifier（Sonnet 5.5） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main（implementer・verifier を含む） | Sonnet 5.5 / Opus 5.5 | 記載なし | 106 | 29,625 | 165,110 | 2,514,577 | 100% |
| 合計 |  |  | 106 | 29,625 | 165,110 | 2,514,577 | 計 2,709,418 |

- `token-usage.py` は implementer・verifier を main と分けて出せなかった。モデル別の内訳は Sonnet 5.5 が 70%、Opus 5.5 が 30%
- 始点は `--since '2026-10-20 05:34:05'`（立てたコミット）。終点は決着の前の記録の時点（実装後の確認までを含む。決着の作業の分は少し足りない）

## きっかけ

両者のピップ数の合計が少ない向きを手前とする推測を正解ファイルで試したら、141 組中 132 組が一致し、残る 9 組が合わなかった。
9 組を点検したところ、すべて正解ファイルの向き（手前の色・home）が写真と逆だった（点検の報告: `archives/agents/TODO-170/truth-check-report.md`）。

## やったこと

- 9 組の向きを点検の表どおりに直した（色だけ 4、色と home 4、home だけ 1）。
  色の入れ替えは `points` の符号反転・bar と off の入れ替え・`bottom_colour` の反転、home の入れ替えは `points` を行の中で左右反転して `home` を反転。
  `read` と `fixed_points` にも同じ変換をした。`cube.at` は盤の物理的な側なので変えない
  - `samples/` の 4 組: `collected-grey-red-top`、`collected-tan-black-side-1`、`collected-cork-green-side`、`photo-orange-black-oblique`
  - `collected/` の 5 組（リポジトリに入らない。手元で直した）: `user-1792130519864-ajxlol`、`user-1792243400742-p1vm5a`、`user-1792161634938-n8fzpw`、`user-1792179058872-xlkxee`、`user-1792407219093-7qrh2u`
- orange-black の 3 組と `collected-cork-green-side` の note を書き直した。orange-black の 3 組は note の「白が手前」と食い違うが、点検の判断（手前は灰色、home=left）で直す（2026-10-20 ユーザーが決めた）
- `recognizer/check_accuracy.py --update` で `accuracy_baseline.json` を書き直した。変わったのは `photo-orange-black-oblique` の home の推測が True → False になった 1 か所だけ（TODO-171 の対象）
- 一致を数える `archives/agents/TODO-170/check_pips.py` を足した。recognizer のコードは変えていないので版は上げていない

## 確かめたこと

- verifier が、9 組の向き・石の数（各 15 個）・samples の 4 組の元との機械的な差分・同じ写真の組どうしの一致・accuracy の基準の差を測った。食い違いなし
- ピップ数の合計が最小の向きが正解と一致する件数（`check_pips.py`、141 組）:
  - 色だけ 2 通り: 141 / 141（直す前は 132）
  - 色 × home の 4 通り: 126 / 141（直す前は 117）
- PR #507 の CI（`pytest`・`accuracy`・`ruff`）が通った

## 残ること

- 色と home の 4 通りで見ると 126/141 しか一致せず、TODO-171 の見込み「140 組すべてで一致する」は成り立たない。残り 15 組は、同点が 5 組、home を入れ替えた向きの方が少ないものが 7 組、色と home を入れ替えた向きの方が少ないものが 3 組。ピップ数だけで home まで推測すると外れる。正解が誤りとは限らない（実害は未確認）。同点の決め方と、home の推測に使う別の手がかりを TODO-171 の着手時に決める
- 組の数は TODO.md の「140 組」ではなく 141 組（`samples/` 87 組 + `collected/` 54 組）だった
- orange-black の「手前は灰色」は、写真を撮った人に確かめるのが確実（点検の報告）

## 分担の振り返り

- **見つけたこと:** verifier が見つけた食い違いはなかった。implementer が「一致 140」の見込みを数え直し、色だけの推測と色 × home の推測を分けて報告したことで、TODO-171 の前提が成り立たないと分かった
- **見込みと食い違った理由:** 担当は見込みどおり。食い違ったのは件数で、「140 組すべてで一致」は色だけの推測の話だった。TODO を立てるときに、4 通りで数えた結果を確かめていなかった
- **次に同じ規模ならどう組むか:** 同じ組（implementer + verifier）で足りる。後の項目の見込みに書く件数は、立てる前に実際のスクリプトで数えておく
