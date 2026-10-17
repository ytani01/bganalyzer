# TODO-119. 全件を流すコマンドの確認が、ファイル名を書いただけで出る

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort high | main（実装）+ verifier（Sonnet 5.5 / medium） |
| 実施 | Opus 5.5 / effort high | main（実装）+ verifier（Sonnet 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | high | 10 | 5,713 | 8,949 | 454,646 | 100% |
| 合計 |  |  | 10 | 5,713 | 8,949 | 454,646 | 計 469,318 |

- verifier は定義のモデルが haiku。11 例を JSON に書いてフックに通すだけなので Sonnet 5.5 に上書きした（effort は定義の medium）
- verifier の分は `token-usage.py` に出なかった。Agent ツールの通知では 26,841 トークン
- `--since` は TODO-114 の作業中に立てたので、その直前のコミット（2026-10-17 15:52:51）から

## きっかけ

TODO-114 の作業中、`sed -n 40,80p recognizer/check_accuracy.py`（読むだけ）で `hooks/full-run-guard.py` の確認が出た。
`.claude/full-runs.txt` の正規表現が、コマンドの文字列のどこにでも当たっていた。

## やったこと

`.claude/full-runs.txt` の 2 つの正規表現の前に `python\S*[ \t]+(?:-\S+[ \t]+)*\S*` を付け、python でスクリプトを起動したときだけ当てるようにした。
`--update` と、引数のある `evaluate.py` を除くのは今までどおり。

## 確かめたこと

verifier がフックに 11 例を通した（[archives/agents/TODO-119/](../agents/TODO-119/)）。当たるべき 5 例と依頼文の 1 例で ask、
`sed`・`rg`・`git log`・`--update`・引数のある `evaluate.py` の 5 例では何も出ない。

## 残ること

- コマンドの文字列を見るだけなので、heredoc や echo の中に python の起動を書いても当たる（verifier が例を書き出すときに実際に出た）。
  シェルの構文を解析しないと防げないので、そこまではしない
- `uv run recognizer/check_accuracy.py` のように python を書かずに起動すると当たらない（このリポジトリの手順には無い形）

## 分担の振り返り

- verifier は食い違いを見つけなかった。main が先に 7 例を試していたので、verifier の分は依頼文の 1 例と python のパスの形だけが増えた
- 見込みどおり
- 正規表現を 1〜2 行変えるだけの項目なら、main が試した例と結果を依頼に書き、verifier には足りない例だけを足させる
