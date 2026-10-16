# TODO-065 の分担

- main: 候補の絵を描いて見せ、選ばれたものを `icon.svg` と PNG にし、版を上げた
- verifier（Haiku 5.5 / medium）: PNG と SVG の一致、maskable の安全領域、版と `CACHE` を確かめた。依頼は `verifier-request.md`、報告は `verifier-report.md`

分担の理由: 絵の差し替えと版の書き換えだけで、実装を別の担当に分けるほどの量が無い。確認は決まった手順なので Haiku にした。
候補を並べた画像は `sheet.sh` で作った。
