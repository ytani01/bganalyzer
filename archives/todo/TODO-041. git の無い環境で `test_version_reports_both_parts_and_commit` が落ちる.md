# TODO-041. git の無い環境で `test_version_reports_both_parts_and_commit` が落ちる

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort medium | verifier（Sonnet 5.5 / medium。git の有る環境と無い環境で走らせ、壊すと落ちるか） |
| 実施 | Opus 5.5 / effort 記載なし | verifier（Sonnet 5.5 / 定義の effort） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | 記載なし | 32 | 9,182 | 15,272 | 1,401,202 | 94% |
| verifier | Sonnet 5.5 | 定義の値 | 8 | 100 | 23,509 | 63,436 | 6% |
| 合計 |  |  | 40 | 9,282 | 38,781 | 1,464,638 | 計 1,512,741 |

- main の分には、同じ時間に進めた TODO-028 の調べ（Pi で k-means の種を変えて四隅を測る）が入っている
- verifier はモデルを sonnet に上書きした

## きっかけ

Pi で常駐用のイメージを使って `pytest` を走らせると、イメージに git が無いので `FileNotFoundError` で落ちていた（2026-10-14）。

## やったこと

`analyzer/test_api.py` の `test_version_reports_both_parts_and_commit` で、版の比較のあと、git が無ければ commit を比べずに skip する。
`/version` の `commit` を `.git` のファイルから読む `git_commit` は、別のテストで確かめている。

## 確かめたこと

verifier（archives/agents/TODO-041/verifier-report.md）: git の無いイメージでは skipped、PATH の先頭に偽の git を置くと比較が走って落ちる。
analyzer 全体の失敗は `test_corners_are_found_on_samples` の 1 件だけ（TODO-028）。

## 分担の振り返り

- verifier は、比較がまだ生きていること（偽の git で落ちる）まで確かめた。見つけた問題は無い
- 見込みどおり
- 次も 1 行のテストの直しなら、main の実装 + verifier（Sonnet）でよい。依頼に手順のコマンドまで書いたので、verifier の分は 6% で済んだ
