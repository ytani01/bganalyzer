# TODO-114. 集めた写真のサンプルへの取り込みを自動にする

| | main | 担当 |
|---|---|---|
| 見込み | Opus 5.5 / effort high | main（設計・実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |
| 実施 | Opus 5.5 / effort 不明（記録に残らない） | main（設計・実装）+ reviewer（Opus 5.5 / high、3 回）+ verifier（Haiku 5.5 / medium）+ verifier（Sonnet 5.5 / medium、本番の 1 回）+ general-purpose（Sonnet 5.5、マージ） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | 不明 | 560 | 155,930 | 744,521 | 37,242,965 | 83% |
| reviewer | Opus 5.5 | high | 154 | 12,862 | 349,274 | 5,182,342 | 12% |
| verifier（Haiku・Sonnet） | Haiku 5.5 / Sonnet 5.5 | medium | 116 | 11,555 | 281,062 | 1,845,478 | 5% |
| 合計 |  |  | 830 | 180,347 | 1,374,857 | 44,270,785 | 計 45,826,819 |

- 本番の 1 回とマージの待ちは、利用者に「そういう処理はサブエージェントにやらせて」と言われて担当に回した。本番の 1 回は verifier を Sonnet 5.5 に上書きした（PR とログを読む判断があるため）。マージは verifier が直せない定義なので general-purpose（Sonnet 5.5）にした
- 集計の終点は #349 のコミット（20:18）で、そのあとに動いた本番の 1 回とマージの担当の分は一部しか入っていない。サブエージェントの分は少なめに出る

## きっかけ

「サーバーに保存する」で `collected/` にたまった写真と直した盤面を、`samples/collected-*` に入れるのは手作業だった（TODO-030）。マージまで自動にする（2026-10-17 ユーザーが決めた）。

## やったこと

- `recognizer/import_collected.py` を足した。`collected.py` が測り直したあと、読み違いのある組を古い順に 10 組まで選び、`origin/main` の別の worktree で `samples/collected-<id>` に書き、`accuracy_baseline.json` と `recognizer/README.md` の「精度」の表を書き直して PR を作る。チェックが通り、最新の main を取り込んでも通ればマージする
  - 除くもの: `samples/` に同じ id があるもの、`samples/` か取り込み済みの組と同じ写真（バイト列の sha256）、画像として読めないもの、認識が「読めなかった」組、id が空のもの・末尾が同じ id
  - 写真は背景の塗りつぶし処理で盤の外（正解の四隅の外）を黒くし、EXIF なしで書き直す。truth.json は今のサンプルにある項目だけを書く（誰でも送れるため。利用者が決めた）
  - 前の取り込みの PR が開いていれば何もしない（利用者が決めた）。SIGTERM（サービスの再起動）でも worktree を消し、`import.log` に書く
- 動くのは `BG_IMPORT` を設定したサーバーだけ（開発機。誰でも送れる Pi では動かさない。利用者が決めた）。開発機は `systemctl --user edit` で `Environment=BG_IMPORT=1` を足した
- `collected.valid` で四隅の NaN・inf を弾くようにした
- アプリの「読み取りの改善」の説明に「読み違えた写真は、盤の外を黒く塗って公開のサンプルに入れることがある」と足し、analyzer を 0.67.0 にした（利用者が決めた）
- `CLAUDE.md`・`README.md`・`docs/raspi.md`・`docs/HANDOVER.md`・`samples/CREDITS.md`・`recognizer/README.md`・`analyzer/README.md` を書き換えた
- 本番の 1 回で、自動で入った斜めの写真（`collected-gka56t`）が `test_steep_photo_is_flagged` の手で並べた一覧に無く落ちた。自動で入れた組（note に added automatically）はその照合から外した（#349）
- PR: #347（道具）、#349（テストの直し・言い方）、#348（自動の取り込みの 1 回目、10 組）

## 確かめたこと

- `analyzer/test_collected.py` に、選ぶ条件・背景の塗りつぶし処理・項目の絞り込み・`BG_IMPORT` の有無・「読めなかった」組・NaN/inf・`merge()` の待ち直しと `--match-head-commit` を足した。reviewer が 1 か所ずつ壊して落ちることを確かめた（`archives/agents/TODO-114/reviewer-report*.md`）
- verifier（Haiku）が、`collected/` の本物の 3 組で、写真の大きさが変わらないこと、盤の外が黒く盤が欠けていないこと、項目が落ちないことを確かめた（`verifier-report.md`）
- 開発機で 1 回動かし、10 組の PR #348 ができた。テストを直したあと main を取り込んでマージされ、開発機の `/version` が c6ed3e4 になった（`local-report.md`、`merge-report.md`）。入った 10 枚は利用者も見た

## 残ること

- サーバーのチェックアウトが `origin/main` より古いと、測り直しで選んだ組を `check_accuracy.py --update` が扱えず、取り込みが毎回止まることがありうる（理由は `import.log`）。開発機は pull のたびに再起動するので手当てしていない
- `_run`（開いた PR があるとき、`gh pr create` の失敗）と `except BaseException` にはテストが無い（偽の `git`・`gh` を一式そろえる手間に見合わないと見た）

## 分担の振り返り

- **reviewer**: 1 回目で、Pi でも動いてしまうこと、送られた truth.json の余分な項目がそのまま公開されること、読めない写真で以後の取り込みが止まること、マージ後のブランチ削除が毎回失敗すること、README の表の行に正規表現が合わないことなど、要修正 4 件・検討 8 件を見つけた。2 回目で、認識が例外で止まる組で取り込みが止まること、3 回目でテストの lambda が何も確かめていないことを見つけた。利用者の判断が要る点（動かす機械・項目・残った PR・アプリの説明）は、どれも reviewer の指摘から出た
- **verifier（Haiku）**: 本物の組での背景の塗りつぶし処理と項目を確かめた。食い違いは無かった
- **本番の verifier（Sonnet）**: テストの失敗を見つけた。これは手で並べた一覧という、差分の外の前提で、reviewer の範囲では見つからなかった
- **見込みとの食い違い**: reviewer が 3 回になった。1 回目の指摘で利用者の判断が 4 つ要り、直しが大きくなったため。本番の 1 回とマージの待ちを担当に回したのは、利用者に言われてから
- **次に同じ規模なら**: 公開されるデータや外へ書く処理（push・マージ）を作る項目では、立てるときに「どの機械で動かすか」「送られたデータのどの項目を出すか」「失敗して残ったものをどう扱うか」を先に利用者に聞く。reviewer の 1 回目を待たずに済み、直しが 1 回減る。本番の 1 回とマージの待ちは、最初から担当（Sonnet）に回す。差分の外の前提（サンプルの名前を並べたテストなど）は、`samples/` を増やす項目では reviewer の依頼に「`samples/` の名前を持つテスト」を `git grep` で挙げさせる 1 行を足す
