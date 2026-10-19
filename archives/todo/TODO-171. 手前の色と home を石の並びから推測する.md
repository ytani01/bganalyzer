# TODO-171. 手前の色と home を石の並びから推測する

| | main | 担当 |
|---|---|---|
| 見込み | Opus 5.5 / effort high | implementer（Opus 5.5 / medium）+ reviewer（Opus 5.5 / high）+ verifier（Sonnet 5.5 / medium）。reviewer を先に回す |
| 実施 | Opus 5.5 | implementer（Opus 5.5 / medium）+ reviewer（Opus 5.5 / high、2 回）+ verifier（Sonnet 5.5 / medium）+ ローカルの確認の verifier（Sonnet 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5・Sonnet 5.5 | 記録に残らない | 540 | 150,995 | 569,847 | 18,267,644 | 100% |
| 合計 |  |  | 540 | 150,995 | 569,847 | 18,267,644 | 計 18,989,026 |

- `token-usage.py TODO-171 --since '2026-10-20 05:43:16'`（TODO-170 を決着させたコミットの時刻）で数えた。立てたコミットは TODO-170 と同じなので始点を `--since` で渡した
- teammate の分も `main` の 1 行に入っている（モデル別では Opus 5.5 が 91%、Sonnet 5.5 が 9%）。同じ時間に TODO-172〜174 も進めていたので、その分も混ざっている。終点は `token-usage.py` が選んだ de4657e（06:10:40）で、そのあとのマージ・ローカルの確認・決着の分は入っていない
- 担当の effort は、そのときの定義（`~/.claude/agents/*.md`）のまま。implementer・verifier は定義のモデル（sonnet・haiku）を Opus 5.5・Sonnet 5.5 に上書きした

## きっかけ

手前の色を取り違えると、PIP が 262/325 のような値になる（2026-10-20 ユーザーの報告）。PWA は端末に覚えた色で写真を読んでいた。

## やったこと

決めたこと（2026-10-20 ユーザーが決めた）: 手前の色は、両者のピップ数の合計が少ない側にする。home は今の `home_prior` のまま変えない。recognizer の読み取りの後に、home の `auto` と同じ形で色にも `auto` を足す。PIP をタップして入れ替える操作は残す。「4 通り（色 × home）でピップ数が最少」をそのまま使う案は採らない。

- `recognizer/board.py`（0.29.0）: `guess_bottom()` を足し、`bottom_colour="auto"` なら home の推測より先に色を決める。home も `auto` のときは、色ごとに左右の少ない方のピップ数で比べる（左右を `right` に決めて比べると、正解の盤面 141 組 × 4 通りで 449 しか戻らない。この順では 538）。同点なら明るい方を手前にする。`info` に `bottom_colour` と `colour_guess` を足した
- `analyzer/app.py`（0.93.0）: `/analyze-photo` の `bottom_colour` に `auto` を足し、応答に推測した色を返す
- `analyzer/static/app.js`: `colourPick` を足し、新しい写真は `auto` を送って推測した色を使う。PIP のタップと置き場のタップで、画面に出ている色を決まったものにし、読み直しで推測し直さない（置き場の分はレビューの指摘。2026-10-20 ユーザーが決めた）。「手で盤面を作る」は直前の写真で読んだ色で始める（2026-10-20 ユーザーが決めた）
- `recognizer/README.md`・`analyzer/README.md` に `auto` と決め方を書いた
- テスト: `analyzer/test_api.py`（色の推測、同点、両側で比べる、API の `auto`）、`analyzer/test_pwa.py`（新しい写真で `auto` を送る、タップで色が決まる）
- `archives/agents/TODO-171/check_guess.py`: 正解の盤面から一致を数えるスクリプト

## 確かめたこと

- 正解の盤面 143 組（samples 87・`collected/` 56）× 4 通り = 572 通りで、home が正解なら色は 572 すべて、home も推測すると 546 が正解に戻る（verifier-report.md）。外れるのは 9 組（色も home も逆にした方がピップ数が少ない 3 組、同点の 5 組、`home_prior` が外れる 1 組）
- レビュー 2 回（reviewer-report.md・reviewer-report-2.md）。足したテストは、壊すと落ちることを確かめた
- [x] ローカル: 色を逆に置いた写真で、手前が正しく選ばれるか → 期待どおり（analyzer 0.93.0、recognizer 0.29.1）。端末に逆の色を覚えさせて読ませた 2 枚（collected-app-green-far・collected-app-green-shot）で、手前の色が正解どおりになった。置き場をタップしてから読み直しても色は変わらなかった（local-report.md）

## 残ること

- home も推測するときに外れる 9 組（上のとおり）は、ピップ数だけでは決められない。同点のときに画面で知らせる表示も作っていない

## 分担の振り返り

- **各担当が見つけたこと:** implementer は、指示の前提「141/141 組が一致」が home を正解にしたときだけの数で、home も推測すると色と home の決める順で結果が変わることを測って見つけた。reviewer（1 回目）は、PWA の使い方の README が古いこと、置き場のタップのあとの読み直しで色が変わりうること、テストが無い分岐 3 つ、`pips()` の重複を見つけた。reviewer（2 回目）は、置き場のテストが暗い駒の場合しか見ていないことだけを挙げた。verifier は一致件数を測り直して食い違いが無いことを、ローカルの確認は実際の画面で色が選ばれることを確かめた
- **見込みと食い違った理由:** reviewer が 2 回、ローカルの確認の担当が 1 人増えた。1 回目のレビューで PWA の挙動の判断（手で盤面を作るとき・読み直し）が出て、直したあとに確かめ直すことになったため
- **次に同じ規模なら:** PWA の状態（何を端末に覚え、何を写真ごとに残すか）が変わる項目では、implementer への依頼に「タップ・読み直し・手で入れる」の 3 つの経路での扱いを先に書く。書いておけば、レビューの 2 回目は要らなかった
