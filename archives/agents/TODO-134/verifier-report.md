# TODO-134 確認報告（verifier）

コードは変更していない。走らせたのは検証のスクリプトと pytest だけ。

## 1. pytest（1 ファイルずつ）

- `uv run pytest -q analyzer/test_side.py -k find_corners`: 2 passed, 14 deselected, 終了コード 0
- `uv run pytest -q analyzer/test_api.py -k find_corners`: 1 passed, 48 deselected, 終了コード 0

一致。

## 2. 実際の API（TestClient、`POST /find-corners`、フィールド image だけ）

スクリプト: `/home/ytani/work/bganalyzer/archives/agents/TODO-134/verify.py`（終了コード 0）

| 写真 | status | side | corners 点数 | かかった秒数 |
|---|---|---|---|---|
| 横から（photo5 を ROTATE_90_CLOCKWISE、長辺 2048px に縮小、1538×2048） | 200 | "right" | 4 | 3.63 |
| 正面（photo2 を長辺 2048px に縮小、2048×1538） | 200 | null | 4 | 0.58 |

- 横から: corners = [[1046.7, 688.8], [1340.6, 1388.9], [317.3, 1409.3], [333.4, 603.2]]
- 正面: corners = [[438.2, 149.5], [1611.9, 173.0], [1752.0, 1224.3], [399.0, 1338.4]]
- 応答のキーは `corners`, `height`, `side`, `width`

一致。`side` は横からの写真で "right"、正面の写真で null に分かれた。

## 3. バージョン

- `analyzer/app.py` の `__version__` = "0.74.0": 一致
- `analyzer/static/app.js` の `APP_VERSION` = "0.74.0": 一致
- `recognizer/board.py` の `__version__` = "0.25.0": 一致

## 4. 変更ファイル（`git status` と `git diff main --stat`）

未コミットの変更: TODO.md, analyzer/README.md, analyzer/app.py, analyzer/static/app.js, analyzer/test_api.py, analyzer/test_side.py, recognizer/README.md, recognizer/board.py, recognizer/side.py（9 files, 79 insertions, 15 deletions）。未追跡: archives/agents/TODO-134/。

変更範囲は TODO-134 の内容（find-corners の side 判定、版の上げ、テスト、文書、TODO.md）と合っている。指示に無いファイルの変更は見つからなかった。中身の diff の読み込みは範囲外としたため、ここでは行っていない。

## 確かめられなかったこと

- 他のサンプル、精度、テスト全体は指示どおり見ていない。
- 横から撮った写真の 4 点が実際に盤の四隅かどうかは、この確認では見ていない（side の値と点数だけを確かめた）。
- 判断が要る点は無い。
