# TODO-105 の分担

- main: 測定・試作・実装（試した案と結果は recognizer/README.md の四隅の推定の節）
- reviewer（Opus 5.5 / high）: `recognizer/corners.py` の差分を、挙動と設計に照らして見る。挙動と分岐が変わるので立てる
- verifier（Haiku 5.5 / medium）: reviewer のあとで、テストが「壊すと落ちる」か、記録した数字が再現するかを確かめる

## 置いてあるもの

- `full_corners.py <出力.json>`: 全サンプルの `check_corners.measure` を元の大きさと `--app` で測り、時間とともに JSON に書く
- `full-main.json` / `full-new.json`: main（8410215）と新しいコードでの結果（2026-10-18、main が測った）
- `read_points.py <サンプル名>...`: 目視・今の推定・新しい推定の四隅から読めたポイントの数（今の推定は `W_ALONG = 0` と差し替え無しで作る）
- `side_choice.py <recognizer のディレクトリ> <出力.json>`: 全サンプルで `find_corners_any` が横からの探し方に回ったか。`side-main.json` / `side-new.json` が main と新しいコードの結果で、判定が変わったものは無い（どちらも 67 枚中 13 枚。reviewer の指摘を受けて main が測った）
