# TODO-012 の分担

2 回目（recognizer 0.5.1、2026-10-13、Raspberry Pi）だけ編成した。1 回目（0.3.1）はクラウドの別セッションで、main のみ。

| 担当 | 見たところ | 理由 |
|---|---|---|
| main | leather-cups の原因の切り分けと board.py の実装 | 原因が分からないと直し方が決まらず、実装と切り離せない |
| reviewer | 差分が分岐の意味を変えていないか、しきい値の余裕、文書と実測の食い違い | 分岐としきい値が変わる項目なので、確認とは別に「良いか」を見る |
| verifier | evaluate.py の前後比較、壊すと落ちるか、文書の数字の再現 | 実装した本人は「動くはず」で済ませやすい。手順が決まっているので Sonnet 5.5 |

報告: [reviewer-report.md](reviewer-report.md)、[verifier-report.md](verifier-report.md)。
直す前の測定値: [evaluate-pi-0.5.0.txt](evaluate-pi-0.5.0.txt)。
