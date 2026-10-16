# TODO-066 の分担

| 担当 | 受け持ち | 理由 |
|------|----------|------|
| main | gnubg の下調べ、依頼、まとめ | 前提（マッチの渡し方）を先に測った |
| implementer（Opus 5.5 / medium） | API・engine・PWA・テスト・README | engine・API・PWA の 4 画面・テストにまたがる |
| reviewer（Opus 5.5 / high） | 差分のレビュー | 評価の条件とキューブ判断の分岐が変わる |
| verifier（Sonnet 5.5 / medium） | API と PWA での確認 | 4 画面で入力が残るか、解析し直すかは操作しないと分からない |

## main の下調べ（2026-10-16、gnubg 実測）

- `gnubg.cube_info(value, owner, move, matchto, (score_on_roll, score_opp), crawford, bgv)`。
  `matchto=0` がマネー。マッチでは `jacoby` が 0 になり、`gammonprice` がスコアで変わる
- `hint`（キューブ判断）は gnubg のコマンドで状態を作る:
  `new match N` → `set score A B`（A が player 0 = 手番）→ `set crawford on|off`。
  - `set score` で片方が N-1 になると、gnubg は既定で post-Crawford にする。クロフォードの試合は `set crawford on` が要る
  - クロフォードの試合では `hint` が `You cannot double.` を返す（今の `_parse_cube_hint` は None を返す）
  - **マネーへ戻すのは `new session`**。`new game` はマッチのまま続く
  - マッチでは proper の文に `Optional double, take` が出ることがある
- 依頼: [request.md](request.md)
