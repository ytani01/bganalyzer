# TODO-083 の分担

| 担当 | モデル / effort | 担当したこと | 報告 |
|------|----------------|--------------|------|
| main | Opus 5.5 / high | 原因の測定（photo6 の各段階の四隅・列・三角）、実装、README・版・基準の更新 | － |
| reviewer | Opus 5.5 / high | `fit_columns` に足した分岐が方針どおりか、既存の補正との兼ね合い | [reviewer-report.md](reviewer-report.md) |
| verifier | Haiku 5.5 / medium | photo3〜6 の評価、photo6 の列の位置、補正を外すと 8/24 に戻るか | [verifier-report.md](verifier-report.md) |

分担の理由: 分岐が変わる項目なので、確認とは別にレビューを入れた。reviewer を先、verifier を後に回した。
verifier の確認は手順が決まっていて判断が要らないので Haiku 5.5 にした。
`probe_fit_columns.py` は verifier が列の位置を測ったスクリプト。
