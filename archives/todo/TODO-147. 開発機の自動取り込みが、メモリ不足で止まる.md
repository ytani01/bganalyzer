# TODO-147. 開発機の自動取り込みが、メモリ不足で止まる

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort high | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |
| 実施 | Opus 5.5 / effort high | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | high | 32 | 6,747 | 43,421 | 1,056,249 | 79% |
| reviewer | Opus 5.5 | high | 16 | 81 | 44,235 | 247,485 | 21% |
| verifier | Haiku 5.5 | medium | － | － | － | － | － |
| 合計 |  |  | 48 | 6,828 | 87,656 | 1,303,734 | 計 1,398,266 |

- 集計の範囲は 51522e1 まで。verifier はその後に動いたので入っていない。PR のマージとローカルの `--force` の確認の分も入っていない
- reviewer と verifier の effort は Agent ツールで定義と同じ値を指定した

## きっかけ

2026-10-19 に `collected.py collected --force` を 2 回流し、2 回とも `earlyoom` に止められた。取り込みが worktree で流す `check_accuracy.py --update` が全サンプルを CPU の数（16）だけ並行して読み、1 つ 300〜400 MiB 使う。`import.log` には `CalledProcessError` としか出なかった。

## やったこと

- `recognizer/check_accuracy.py` に `--jobs=N` を足した（付けなければ今までどおり CPU の数だけ並行）
- `recognizer/import_collected.py` の取り込みでは `--jobs=2` で流す。落ちたときは例外の stderr の末尾 20 行を `import.log` に残す。stderr は `errors="replace"` で読む（レビューの指摘）
- `analyzer/test_collected.py` に、stderr の末尾が `import.log` に残ることのテストを足した

## やらないと決めたこと

- 親が止められたときに残る測定の子プロセスは手当てしない。2 つずつにしたので、残っても 2 つまで

## 確かめたこと

- `analyzer/test_collected.py` が通る。stderr を残す行を戻すと新しいテストが落ちる。`--jobs=` を付けないと `None`、`--jobs=2` で 2 が `measure_all` に渡る（verifier）
- ローカル: PR #434 のマージ後に `--force` を流し、メモリ不足で止まらずに PR #435 を作ってマージまで進んだ（2026-10-19 12:39）

## 分担の振り返り

- reviewer は、`text=True` にしたことで stderr が読めない文字のときに `UnicodeDecodeError` になることを実際に試して見つけた。子プロセスが残る件が手当てされていないことも指摘した
- verifier はテストの強さと `--jobs=` の解釈を実測し、問題は無かった
- 見込みと実施は同じ。この規模（2 ファイルで数行）なら次も同じ組み方でよいが、verifier の依頼は 3 項目に絞ったまま短く保つ
