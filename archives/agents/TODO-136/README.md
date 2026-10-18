# TODO-136 の分担

| 担当 | 任せたこと | 報告 |
|---|---|---|
| main | 設計、学習の道具と学習、案 1 の実装、`check_corners.py` の測定、文書 | `check_corners-*.txt`、`compare_ways.*` |
| implementer | 予定の形（YOLO の範囲を先に探す）の `locate` と `find_corners`、版、README | `implementer-brief.md`・`implementer-report.md` |
| reviewer | 最終の差分を規約と設計に照らす | `reviewer-brief.md`・`reviewer-report.md` |
| verifier | テスト、テストを壊すと落ちるか、全サンプルの測り直し、時間 | `verifier-brief.md`・`verifier-report.md` |

分担の理由: `cv2.dnn` の前処理と `find_corners` の分岐は込み入るので implementer（Opus）、挙動が変わるので reviewer を別に入れた。
verifier は測る手順が決まっているので Sonnet。

測定のファイル（すべて `check_corners.py` の全サンプル）:

- `check_corners-before.txt`: 今まで（recognizer 0.26.1）
- `check_corners-after.txt`: YOLO の範囲だけを先に探す形（1 回目のモデル）
- `check_corners-hint.txt`: 案 1（1 回目のモデル、`HINT_FREE` 0.08）
- `check_corners-hint-rf.txt`: 案 1（Roboflow を足したモデル、四隅の順をそろえる直しの前）
- `check_corners-verify.txt`: 最終（verifier が測った）

`compare_ways.py` は途中で 2 案（点数の高い方 / 弱いときだけ YOLO）を比べた道具。そのときの `locate` は範囲を返していたので、今の `corners.py` では動かない。
