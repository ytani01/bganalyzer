# TODO-136 implementer への依頼

ブランチ `claude/yolo-corners`（コミットはしない。main が見てからコミットする）。

## 目的

`recognizer/corners_model.onnx`（YOLO11n-pose、入力 1×3×640×640、出力 1×17×8400 = cx, cy, w, h, conf, 4 つの (x, y, 見える度合い)。
キーポイントの順は TL, TR, BR, BL）を OpenCV の `cv2.dnn` で動かし、盤のおおよその位置を当てて、その周りだけを `corners.py` に探させる。
今あるモデルは 1 エポックだけの仮のもの（中身は当てにならない）。main が学習し直して差し替える。形は変わらない。

## 変えること

1. `recognizer/corners.py` に、写真から crop の範囲 `(x0, y0, x1, y1)` か None を返す関数を足す
   - レターボックス（縦横比を保って 640 に縮め、余白を 114 の灰色で埋める）→ `cv2.dnn.blobFromImage(..., 1/255, swapRB=True)` → forward
   - conf の最も高い 1 つを取り、0.25 未満なら None
   - 4 つのキーポイントを元の写真の画素へ戻し、それを囲む範囲を縦横に 15% ずつ広げる（`check_corners.py --crop` と同じ広げ方）
   - モデルは初めて使うときに 1 回だけ読む。`forward` は同時に呼ばれないよう `threading.Lock` で囲む（API がスレッドから呼ぶことがある）
2. `find_corners` で、`crop` も `search` も無く、`fixed` に 1 つも点が無いときだけ、上の範囲を crop として探す。
   その範囲で見つからなかったとき（YOLO が None のときも）は今の探し方（写真全体）に戻る
   - `fixed`・`crop` があるとき、`side.py` の `search` があるときは今のまま（YOLO を使わない）
3. `recognizer/board.py` の `__version__` を 0.26.1 → 0.27.0
4. `recognizer/README.md` の「四隅の推定」の節に、YOLO で範囲を絞ってから探すこと・見つからなければ全体を探すこと・
   モデルの作り方（`recognizer/train_corners.py`。docstring に手順がある）を 2〜4 行で足す。依存（numpy、opencv）は増えないことも
5. `analyzer/test_api.py` の `test_corners_keep_the_fixed_ones_and_look_in_the_trimmed_part` にある
   `assert find_corners(img) is None`（collected-sj1vrx: 盤が小さく写真全体では見つからない）は、YOLO で見つかるはずの場面。
   仮のモデルではどちらになるか分からないので、**このテストは今は直さない**。main が本番のモデルに替えてから決める

## 保つもの

- `find_corners` の引数と戻り値、progress の段階（edges・uprights・candidates・corners）、四隅を `exact.snap` で丸めること
- 依存（`pyproject.toml`）は変えない。torch・ultralytics・onnxruntime を import しない
- コードの書き方は `corners.py` の周りに合わせる（英語の短い docstring、定数は上にまとめる）

## 確かめること

- `uv run python -c` で 1 枚（例: samples/photo2）に新しい関数をかけ、例外なく範囲か None が返ること（仮のモデルなので中身は問わない）
- `uv run pytest analyzer/test_api.py -k corners` を 1 回流し、結果を書く（仮のモデルなので落ちても直さない。落ちたテストの名前だけ書く）
- 全サンプルの `check_corners.py` は流さない（main が本番のモデルで流す）

## 報告

`archives/agents/TODO-136/implementer-report.md` に、変えた点・確かめた結果・残る懸念だけを書く。
返事は「終わったか・報告ファイルのパス・判断が要る点」だけ。
