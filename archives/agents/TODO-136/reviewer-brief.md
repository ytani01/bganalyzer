# TODO-136 reviewer への依頼

worktree `/home/ytani/work/bganalyzer-todo136`（ブランチ `claude/yolo-corners`、未コミット）の差分をレビューする。コードは直さない。

## 対象

`git status --short` と `git diff` に出るもの。中心は `recognizer/corners.py`（`locate`、`guess` の `hint`、`_swap` の引数、`find_corners`）と `recognizer/train_corners.py`（新規）。
`analyzer/test_api.py` の 1 か所、`recognizer/README.md`・`samples/CREDITS.md`・`TODO.md` の TODO-136 も。

## 決まっていること（ここは問わない）

- YOLO11n-pose を ONNX にして `cv2.dnn` で動かす。依存は増やさない
- 写真全体を探し、候補の四隅がモデルの四隅から長辺の `HINT_FREE`（8%）より離れていれば `HINT_WEIGHT` × 超えた分だけ点数を下げる。見つからなければモデルの四隅の外接矩形 +15% を crop として探し直す
- `fixed`・`crop`・`search`（side.py）があるときは YOLO を使わない
- 値（8%、4.0）は数枚で選んだもの。調整の良し悪しは問わない

## 見てほしいこと

- `find_corners` の分岐: hint の有無、`search` との関係、見つからないときの探し直し（再帰が止まるか）、progress の段階
- `_swap` と `guess` で、点数の比べ方が揃っているか（hint の罰が片方だけに効いていないか）。MIN_SCORE との比べ方
- `locate` のレターボックスと座標の戻し方、スレッドの扱い、モデルが無い・壊れているときの振る舞い
- `train_corners.py` の `order`（四隅の並べ方）と `add_coco`
- 文書（README、CREDITS、TODO.md）がコードと食い違っていないか

## 見なくてよいもの

- 全サンプルの精度（main が測った: `archives/agents/TODO-136/check_corners-*.txt`）。測り直さない
- `archives/agents/TODO-136/compare_ways.py`（途中の試しの道具で、今の `locate` の戻り値とは合わない。記録として残す）
- 境界線上の判断は報告だけ。実害が未確認なら「実害は未確認」と添える

## 報告

`archives/agents/TODO-136/reviewer-report.md` に、指摘（重さ順、ファイルと行、なぜ問題か）だけを書く。問題が無い項目は 1 行。
返事は「終わったか・報告ファイルのパス・判断が要る点」だけ。
