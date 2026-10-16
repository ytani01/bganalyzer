# TODO-099. マッチのスコアを盤に出し、読み上げでは読まない

| | main | 担当 |
|---|---|---|
| 見込み | Opus 5.5 / effort medium | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |
| 実施 | Opus 5.5 / effort medium | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | medium | 76 | 17,524 | 40,621 | 3,375,779 | 82% |
| reviewer | Opus 5.5 | high | 34 | 137 | 90,624 | 680,160 | 18% |
| 合計 |  |  | 110 | 17,661 | 131,245 | 4,055,939 | 計 4,204,955 |

- 集計の終点は `matchText` を消したコミット（9333106）で、そのあとに動いた verifier（Haiku 5.5 / medium）の分は入っていない。TODO-100 と時間が重なっていて、main の分には TODO-100 を立てたやり取りも入っている
- effort は `~/.claude/agents/reviewer.md`・`verifier.md` の値（上書きしていない）

## きっかけ

ユーザーの依頼（2026-10-17）。スコアは画面を見れば分かるので読み上げない。代わりに、盤面の確認と解析結果の盤の絵にスコアを出す。

決めたこと（ユーザー）: 各自のスコアは自分の行のホームと反対の端（キューブの内側。キューブが無い側も同じ位置）。何ポイントマッチかとクロフォードは、奥の行のさらに上に 1 行足して中央に出す。マネーゲームでは何も出さない。

## やったこと

- `analyzer/static/board-view.js`: scene に `match` を足し、マッチのときだけ viewBox を上へ 26 伸ばして `drawMatch` で「7 ポイントマッチ（クロフォード）」の行と「3 点」の札を描く。マネーゲームの盤の絵は変わらない
- `analyzer/static/app.js`: 盤の絵の scene に `s.match` を渡し、依存にも足した。`style.css` に `.match-n`
- `analyzer/static/result.js`: `speechText` からスコアを外し、使わなくなった `matchText` を消した（結果の画面のマッチの文はサーバーの `summary` から来ていて、`matchText` は使っていなかった。立てたときの「画面の表示はそのまま」は前提の誤り）
- `analyzer/test_pwa.py`・`analyzer/README.md` を直し、analyzer を 0.61.0 にした（PR #303）

## 確かめたこと

- reviewer: 要修正 0 件（`archives/agents/TODO-099/reviewer-report.md`）。`matchText` が使われなくなる点を挙げ、消した
- verifier: ブラウザで viewBox（マネーゲーム `0 -38 660 516`、マッチ `0 -64 660 542`）、札の位置と重なり、home の左右、結果の画面、読み上げにスコアが入らないことを実測（`archives/agents/TODO-099/verifier-report.md`）
- ユーザーが画面の画像を見て OK した。マージ後のローカルで `measure.py` を流して同じ結果

## 分担の振り返り

- reviewer は TODO の前提の誤り（`matchText` は画面に使われていない）を見つけた。verifier は食い違いを見つけなかった。挙げた viewBox の 2 の差は、依頼に書いた値（reviewer の計算を写した）の誤り
- 見込みどおりの編成。食い違いは無い
- 次も同じ規模なら同じ組み方でよい。ただし verifier への依頼に数値を書くときは、コードから計算した値を写さず「今の値を読み出して、マネーゲームで変わっていないこと」と書く（変わっていないことの確認には前の値を測れば足りる）
