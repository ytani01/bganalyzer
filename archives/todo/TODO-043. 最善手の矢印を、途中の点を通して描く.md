# TODO-043. 最善手の矢印を、途中の点を通して描く

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort medium | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Sonnet 5.5 / medium。Playwright で矢印を見る） |
| 実施 | Opus 5.5 | main だけ（実装・テスト・Playwright での確認）。使った量は測っていない |

## きっかけ

「22/15」の矢印が 1 本で、途中で打つのか分からない（実際は 20 を通る打たない手。打つ手は「22/17*/15」で赤い丸が出る）。
決めたこと（2026-10-14、ai1）: ダイス 1 つずつ別の短い矢印で描く（折れ線 1 本にはしない）。打つ所は今どおり赤い丸。

## やったこと

analyzer 0.31.0。

- `analyzer/analysis.py`: `moves[]` に `steps`（ダイス 1 つずつの `[from, to]`、手番の側から数えたポイント、25 = バー、0 = 上がり）を足した。
  gnubg の手のタプルがダイス 1 つずつの組なので、それをそのまま返す（上がりで途切れたタプルを補ったものも同じ）
- `analyzer/static/moves.js`: `BgMoves.hops` が手の文字列のほかに `steps` も受け取る
- `analyzer/static/app.js`: `drawMoveArrows` は `steps` があればそれで 1 歩ずつ矢印を描く。
  `steps` の無い古い結果（履歴に残っているもの）は今までどおり文字列から描く
- `analyzer/README.md` に `steps` と矢印の説明を足した。analyzer と `APP_VERSION` を 0.31.0 に上げた
- テスト: `test_api_moves_have_one_step_per_die`（6-5 の「24/13」が `[[24, 18], [18, 13]]`、3-3 は 4 歩）、
  上がりで補った手の `steps`、`test_move_hops_from_steps`（途中で打つ・バーから・上がり・不正な形）

## 確かめたこと

`uv run pytest analyzer` が通った。ヘッドレスの Chromium（npm の `@sparticuz/chromium`。クラウドでは Playwright のブラウザを取ってこられないため）で PWA を開き、手で局面とダイスを入れて解析した。

- 初期配置・6-5: 「24/13」が矢印 2 本（24→18、18→13）
- 5-2 で 22 と 17 に駒: 1 位「22/17* 13/11」は 2 本で 17 に赤い丸。2 位「22/17*/15」をタップすると 2 本（22→17 に赤い丸、17→15）
- 初期配置・3-3: 「8/5(2) 6/3(2)」が 4 本

Pi で確かめること: PI-023。

## 分担の振り返り

- 見込みでは reviewer と verifier を付けるはずだったが、変更が小さい（API に 1 項目、描き方は既存の 1 歩ずつの処理をそのまま使う）ので main だけで実装と画面の確認をした
