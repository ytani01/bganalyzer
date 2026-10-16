# TODO-098. ダイスを入れたとき、そのロールの Luck を出す

| | main | 担当 |
|---|---|---|
| 見込み | Opus 5.5 / effort medium | main（測定・実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |
| 実施 | Opus 5.5 / effort medium | main（測定・実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | medium | 76 | 22,254 | 39,231 | 5,641,815 | 78% |
| reviewer | Opus 5.5 | high | 44 | 4,084 | 76,214 | 1,113,147 | 16% |
| verifier | Haiku 5.5 | medium | 30 | 144 | 38,360 | 423,364 | 6% |
| 合計 |  |  | 150 | 26,482 | 153,805 | 7,178,326 | 計 7,358,763 |

- TODO-097 の分も含む（同じ PR）。`--since '2026-10-17 07:36:49'`（TODO-098 を立てたマージ）から決着の直前まで
- main の分には、途中で表示例の画像を作った分も入っている
- verifier は呼び出しで `model: haiku` を指定（定義と同じ）

## きっかけ

ユーザーの質問（2026-10-17）「Luck は出せるか」。写真の 1 回のロールの分なら出せるので項目にした。

## やったこと

- `analyzer/engine.py`: `_luck` で、その目の最善手のエクイティから 21 通りの目の最善手のエクイティの確率平均を引く（キューブなし、最大 1 手読み）。動かせない目は盤がそのままで相手が振るとして評価する。初期局面でゾロ目以外のときは gnubg の LuckFirst と同じく、どちらの側にも出えた 30 通りで平均する
- `analyzer/analysis.py`: 結果に `luck`（ダイスが無ければ `null`）
- `analyzer/static/result.js`: 最善手の見出しの下に「Luck +0.329・良い目」、読み上げは最善手のあとに「良い目です。」。区切りは gnubg の `Luck()` と同じく ±0.3・±0.6 を超えたら
- `analyzer/test_api.py`・`analyzer/test_pwa.py`、`analyzer/README.md`
- analyzer 0.60.0

決めたこと（ユーザー）: 画面と読み上げに出す。画面は数字と言葉、読み上げは言葉だけ。21 通りの探索は最大 1 手読み（開発機で初期局面: 1 手読み 0.14 秒、2 手読み 1.28 秒）。

## 確かめたこと

- reviewer（`archives/agents/TODO-098/reviewer-report.md`）: 式・向き・マッチのときの `ci_opp`・動かせない目の評価は合っている。区切りの等号が gnubg と違う、初期局面で gnubg の LuckFirst と値が違う（3-1 で +0.087 と +0.163）、テストが重みの誤りと盤の入れ替えの誤りで落ちない → すべて直した
- verifier（`archives/agents/TODO-098/verifier-report.md`）: 3-1 が +0.163、6-6 が +0.329、ダイスなしは `None`。`_luck` を 2 通り壊すとテストが落ちる。画面と読み上げの並び
- GitHub Actions の test が通ってからマージした（PR #297）
- ローカル: 0.60.0 のサービスで初期局面 6-6 が「Luck +0.329・良い目」

## 分担の振り返り

- reviewer は gnubg のソースと突き合わせて、区切りの等号と LuckFirst の違い、テストの弱さを見つけた。gnubg に揃えるという方針が決まっていたので、利用者に聞かずに直せた。verifier は食い違いを見つけなかった
- 見込みどおり。ただし、最初の実装で gnubg のソースを読まずに式を書いたため、reviewer の指摘のあとで直す 1 巡が増えた
- 次に「gnubg と同じ」と決めた計算を実装するときは、main が先に該当するソースの箇所（今回なら `analysis.c` の `LuckNormal`・`LuckFirst`・`Luck`）を読んでから書く
