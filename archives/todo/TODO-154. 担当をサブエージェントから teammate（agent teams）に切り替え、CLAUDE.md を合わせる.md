# TODO-154. 担当をサブエージェントから teammate（agent teams）に切り替え、CLAUDE.md を合わせる

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort 記載なし | main（判断）+ implementer（Sonnet 5.5 / medium、文書の書き換え）。文書だけの項目なので確認は main |
| 実施 | Opus 5.5 / effort 記載なし | main（判断・書式の確認）+ implementer（teammate、Sonnet 5.5 / effort 記載なし、文書の書き換えと決着） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | 記載なし | 52 | 8,791 | 98,121 | 1,096,973 | 91% |
| implementer | Sonnet 5.5 | 記載なし | 2 | 26 | 200 | 120,624 | 9% |
| 合計 |  |  | 54 | 8,817 | 98,321 | 1,217,597 | 計 1,324,789 |

- 集計は `--since '2026-10-19 22:44:00'`（直前の項目のマージ直後）から決着の直前まで。teammate の会話ログは一部しか拾えておらず、implementer の行は実際より少ない可能性がある（`token-usage.py` が subagents の `.meta.json` を読めず警告を出した）
- implementer は subagent でなく teammate として起動した。この項目が最初の例

## きっかけ

2026-10-19 ユーザーが、担当をすべて teammate（agent teams）にすると決めた。公式ドキュメントでは Agent ツールに `isolation` を付けると teammate にならないので、worktree を Agent ツールで分ける決まりが使えなくなる。

## やったこと

`CLAUDE.md` の「共同開発」を書き換えた。

- main が担当にさせる決まりを、`isolation: "worktree"` から teammate に変えた。teammate は `name` 付きで起動し `isolation` は付けない。bganalyzer だけで有効（`.claude/settings.local.json`、リポジトリには入らない）
- teammate は main と同じトップの作業ツリーで起動するので、作業の最初に自分で `git worktree add .claude/worktrees/<名前> -b claude/<作業内容> origin/main` を作り、その中で編集・コミット・PR まで行う。トップは main のままにする（`bganalyzer.service` がトップを見ているため）
- 同じファイルを複数の担当に同時に編集させない
- tmux で開いた teammate には SendMessage が無いことがあるので、main に確認を頼むときは作業を止めて返事で伝える
- 「サブエージェントに画面を操作させるときも」を「担当（teammate）に〜」に直した

## 確かめたこと

書式は main が確認した。`rg -n "isolation|サブエージェント" CLAUDE.md` で、直した箇所以外に食い違う記述が無いこと。teammate が最初に自分で作業ツリーを作って PR まで進める流れは、この項目の作業そのもので試した（SendMessage が無い問題はここで見つかり、箇条に足した）。
