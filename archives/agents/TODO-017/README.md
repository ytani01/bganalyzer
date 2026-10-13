# TODO-017 の分担

- main（Opus 5.5）: 候補探し、正解の読み取り、README・CREDITS・テストの更新。写真を見て判断する作業なので分けなかった
- verifier（Sonnet 5.5 に上書き / medium）: 正解 3 枚・出典・顔の有無・evaluate の値の突き合わせ。
  突き合わせる対象が 72 ポイントと多く、Haiku では静的な確認に逃げるおそれがあるので Sonnet にした
- 報告: [verifier-report.md](verifier-report.md)
