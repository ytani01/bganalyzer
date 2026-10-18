# TODO-137 の分担と道具

## 分担

- main: 調査（点数・四隅の位置・重なりの測定）と実装
- reviewer（Opus 5.5 / high）: `find_corners_any` の分岐が変わるので、確認とは別にレビューを入れた（報告は `reviewer-report.md`）
- verifier（Haiku 5.5 / medium）: テストの実行、直しを効かなくするとテストが落ちるか、全サンプルの判定の再現（報告は `verifier-report.md`）

## 道具

| ファイル | 中身 |
|---|---|
| `feat.py` | 普通・右・左の四隅の点数、正解とのずれ、普通の四隅との面積比と重なり |
| `part.py` | `side._part` の値（右・左） |
| `side-137.json` | 直した後の `archives/agents/TODO-105/side_choice.py` の結果（直す前は `archives/agents/TODO-105/side-new.json`） |

横から撮った 6 枚（photo5・photo6 を撮ったままの向きに戻したものと、collected の 4 組）は `samples/` に無く、TODO-120 の作業の置き場に残っていたもので測った。
