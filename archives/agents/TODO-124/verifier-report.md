# TODO-124 確認（verifier）

測定: `archives/agents/TODO-124/measure.py`（live_view の窓、samples/screen2.jpg を 1 枚・1 回。analyzer 0.70.1）。
時刻は set_input_files の直前を 0 とした ms。

| 時刻 | 出来事 |
|---|---|
| 123 | cornerGuess = finding |
| 220 | edges を受信 |
| 338 | uprights, candidates を受信 |
| 613 | corners を受信（検出の終わり） |
| 1057 | scan.done() が解決（4 段階を出し終えた） |
| 1073 | cornerGuess = found（四隅の画面の操作が可能） |

- 読み込みから四隅が決まるまで: **約 1073 ms**（変更前は約 2.7 秒）。期待の 1.5 秒以下に収まる。
- 段階が飛ばされていないこと: 4 段階とも受信し、最後の受信（613）から done（1057）まで 444 ms。
  200 ms × 4 = 800 ms の表示が 220 ms 前後から順に流れた時刻と合う。
- 確かめられなかったこと: 各段階が描かれた画面のフレーム自体は抜いていない。「順に描かれた」は受信と完了の時刻からの推定。
- 期待との食い違い: なし。
