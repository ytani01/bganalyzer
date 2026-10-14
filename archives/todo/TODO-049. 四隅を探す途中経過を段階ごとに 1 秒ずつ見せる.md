## TODO-049. 四隅を探す途中経過を段階ごとに 1 秒ずつ見せる

- **担当:** ai1
- **見込み:** main Opus 5.5 / effort medium + implementer（Opus 5.5 / medium）+ reviewer（Opus 5.5 / high）+ verifier（Sonnet 5.5 / medium。Pi のヘッドレスの Chromium で、段階が 1 秒ずつ順に出るか見る）

**問題:** 写真を選んだあとの四隅の自動検出（`/find-corners`、`recognizer/corners.py`）は結果が一度に出るだけ。
PI-029 の「読み取り」と同じように、途中経過を段階ごとに 1 秒ずつ見せてほしい（ai1、2026-10-15）。

- [x] `corners.guess()` の段階（横の線の候補 → 縦の線の候補 → 四角の候補の採点 → 縁を寄せて決定）を `/find-corners` で `stream=true` の NDJSON として返す（`edges` → `uprights` → `candidates` → `corners`。PR #140）
- [x] PWA の四隅の画面で、段階ごとに 1 秒ずつ線や四角を重ねて見せ、最後に四隅を置く（タップで飛ばせる。`scan.js` の仕組みを使う）。
  各段階の長さは `scan.js` の `STAGE_MS` の表で段階ごとに変えられる（ai1 の依頼、2026-10-15）。読み取り中の四隅の合わせ直し 4 回も 1 回ずつ見せる
- [x] 版を上げ（analyzer 0.36.0・recognizer 0.17.0）、`trace_cpu.py --update`、docs/PI_CHECKS.md に PI-031。Pi のヘッドレスの Chromium での確認は PI-031 で

**2026-10-15 に完了:** PI-031 で Pi のヘッドレスの Chromium で段階が 1 秒ずつ出ることを確かめた。
