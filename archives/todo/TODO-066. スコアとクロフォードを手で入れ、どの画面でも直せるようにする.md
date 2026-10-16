# TODO-066. スコアとクロフォードを手で入れ、どの画面でも直せるようにする

| | main | 担当 |
|---|---|---|
| 見込み | Opus 5.5 / effort medium | implementer（Opus 5.5 / medium）+ reviewer（Opus 5.5 / high）+ verifier（Sonnet 5.5 / medium） |
| 実施 | Opus 5.5 / effort medium | implementer（Opus 5.5 / medium）+ reviewer（Opus 5.5 / high）+ verifier（Sonnet 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| implementer | Opus 5.5 | medium | 126 | 3,477 | 311,543 | 6,838,971 | 58% |
| reviewer | Opus 5.5 | high | 62 | 4,170 | 105,255 | 2,241,079 | 19% |
| main | Opus 5.5 | medium | 62 | 11,948 | 172,186 | 2,059,948 | 18% |
| verifier | Sonnet 5.5 | medium | 24 | 104 | 54,003 | 449,403 | 4% |
| 合計 |  |  | 274 | 19,699 | 642,987 | 11,589,401 | 計 12,252,361 |

- 立ててから着手まで空いたので `--since '2026-10-16 22:48:25'` で数えた
- implementer は定義のモデルが sonnet。engine・API・PWA にまたがるので Opus 5.5 に上書きした
- verifier は定義のモデルが haiku。PWA を操作して確かめるので Sonnet 5.5 に上書きした
- サブエージェントの分は少なめに出ている（`token-usage.py` の制約）

## きっかけ

ユーザーの依頼（2026-10-16）。解析はマネーゲームだけで、`engine.py` は `gnubg.cube_info()` を既定のまま使っていた。
決めたこと: 4 画面すべてで直せる。解析結果の画面で直したら解析し直す。初期値は前回の値。マネーゲームに戻せる。

## やったこと

analyzer 0.47.0 → 0.48.0。分担と下調べは [archives/agents/TODO-066/](../agents/TODO-066/README.md)。

- API（`models.py`・`app.py`・`analysis.py`）: マッチの長さ・white と black のスコア・クロフォードを受け、検証する。
  `/analyze-photo` で解析だけが失敗するときは、読み取った盤面を返し、`analysis_error` を付ける
- engine: `cube_info` にマッチを渡す（手番側を先に）。引数なしの `cube_info()` は gnubg が開いているマッチを使うので、マネーでも全部書く。
  キューブ判断は `new match`・`set score`・`set crawford` で作り、マネーへは `new session` で戻す
- 解析結果と読み上げにスコアを出す。マッチでは「有利」の側を勝率で決める。`Optional double` は「ダブルしてもしなくてもよい」
- PWA: ヘッダーにマッチの欄を 1 つ置き、4 画面で同じものを出す。localStorage に残す。解析結果の画面で直すと解析し直す
- テスト（`test_api.py`・`test_pwa.py`）、`analyzer/README.md`、`docs/PI_CHECKS.md` の PI-048

## 確かめたこと

- verifier: API でマネーとマッチの答えが変わる、クロフォードでキューブの判断が出ない、不正なスコアは 422。
  PWA（390x844）で 4 画面に欄が出て値が保たれ、再読み込みでも残り、結果の画面で変えると解析し直し、写真の要求に値が入る。
  クロフォードでキューブの写った写真を読むと、盤面の画面へ進んで日本語で失敗が出る（[verifier-report.md](../agents/TODO-066/verifier-report.md)）
- `uv run pytest analyzer/test_api.py analyzer/test_pwa.py` 64 件が通る。相手側のスコアを入れ替えない・「有利」をエクイティで決める、に戻すと落ちる

## 残ること

- Pi の PWA での確認（PI-048）

## 分担の振り返り

- main: 着手前に gnubg を測り、`new game` ではマネーに戻らない（`new session` が要る）ことと、クロフォードの `hint` の返事を依頼に書いた。implementer は測り直さずに済んだ
- implementer: 引数なしの `cube_info()` が前のマッチを引きずる不具合を、範囲の中で見つけて直した
- reviewer: 「有利」の勝率が 50% を切る見出し、クロフォードの写真で読み取りごと失敗する件、上がりの手の補完を守るテストが無い件を見つけた。どれもテストでは捕まらなかったもの
- verifier: 食い違いなし。「キューブなし」の注記は、cubeless の評価のことで正しい
- 見込みと同じ編成で済んだ。次に同じ規模なら同じに組む。gnubg のような外のエンジンを使う項目では、main が前提を先に 1〜2 回測ってから依頼に書く
