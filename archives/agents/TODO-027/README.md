# TODO-027 の分担

| 担当 | 見たところ | 理由 |
|---|---|---|
| main | 原因の調査（勾配の向きの偏りで駒の有無が分かることを測る）、board.py の実装、しきい値の総当たり、x86_64 でだけ起きた件の調査 | 手がかりを探しながらでないと直し方が決まらず、実装と切り離せない |
| reviewer | 分岐の意味、足した円と `count_from_circles` の整合、README との食い違い | 円を捨てる・足すという分岐が増える項目なので、確認とは別に「良いか」を見る |
| verifier | evaluate.py の main との比較（公開サンプルと ai1 の盤の `collected/`）、同じ円が重なっても落ちないか、壊すと落ちるか、基準ファイル | 手順が決まった実測なので Sonnet 5.5 |

reviewer を先に、verifier を後に回した。reviewer は 1 回目を使用量の上限で途中で止め、main を取り込んでから頼み直した。
verifier は 0f28503 の直しのあとに同じ担当で 2 回目を測った。

- 依頼: [reviewer-request.md](reviewer-request.md)、[verifier-request.md](verifier-request.md)
- 報告: [reviewer-report.md](reviewer-report.md)、[verifier-report.md](verifier-report.md)
- verifier の計測スクリプト: [dup_hough.py](dup_hough.py)。x86_64 の調査に CI で一時的に動かしたもの: [diag_cube.py](diag_cube.py)
