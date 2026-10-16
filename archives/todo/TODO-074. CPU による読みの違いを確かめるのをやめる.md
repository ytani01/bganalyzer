# TODO-074. CPU による読みの違いを確かめるのをやめる

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort high | main（実装）+ verifier（Sonnet 5.5 / medium） |
| 実施 | Opus 5.5 / effort low | main（実装）+ verifier（Sonnet 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | low | 56 | 10,829 | 68,127 | 2,162,768 | 100% |
| verifier | Sonnet 5.5 | medium | — | — | — | — | 集計外 |
| 合計 |  |  | 56 | 10,829 | 68,127 | 2,162,768 | 計 2,241,780 |

- 立ててから着手までに TODO-069 が挟まったので、`--since '2026-10-16 17:14:00'`（この会話の始まり）で数えた
- verifier は作業のコミットのあとに動いたので集計の範囲に入らない。Claude Code の表示では 25,996 トークン
- verifier は定義のモデルが haiku。消し残しの見分け（過去の記録か、手順として残っているか）に判断が要るので Sonnet 5.5 にした。effort は定義のまま medium

## きっかけ

ユーザーの決定（2026-10-16）: これからは CPU の違いを全く気にしない。

## やったこと

- `recognizer/trace_cpu.py`・`recognizer/cpu_reference.json`・`recognizer/tracing.py` を消した
- `board.recognize` と `dice.read_dice` から `trace` 引数と `_trace` の呼び出しを消した
- CPU を比べるテスト（`test_exact.py` の `test_a_sample_reads_like_the_cpu_reference`、`test_api.py` の `test_corners_are_the_same_on_every_cpu`）を消した
- CLAUDE.md の「精度の確認」を、CPU の違いは気にしない・float を使ってよい・Pi と GitHub Actions で分かれたら GitHub Actions に合わせる、に書き換えた。コマンドの一覧と版の節からも `trace_cpu.py` を消した
- `recognizer/README.md`・`docs/HANDOVER.md`・`tune.py`・`check_accuracy.py` の説明と、TODO-067・TODO-072 の前提を合わせた
- recognizer の版は上げていない（読みは変わらない）。今の整数の計算（`exact.py` など）も書き直していない

## 確かめたこと

verifier（`archives/agents/TODO-074/verifier-report.md`）: 消し残しは過去の記録だけ、`board`・`dice`・`tune`・`check_accuracy` の import が通る、PR #234 の `test`（x86_64・arm64）と `accuracy` が通った。

## 分担の振り返り

- verifier は消し残しが無いことと CI の結果を確かめた。食い違いは見つけなかった
- main が手元で `uv run pytest analyzer` を流し始め、ユーザーに止められた。項目では pytest を verifier の分としていて、CI でも同じものが走る。決まり（CLAUDE.md の「共同開発」の、マージ前に手元でも pytest）が重複のもとだったので、別に直す
- 次に同じ規模（消すだけで、挙動の変わらない項目）なら、main が実装し、verifier には消し残しと CI の結果だけを見させる。テストは CI に任せ、手元では流さない
