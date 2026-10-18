# TODO-136 verifier 報告

1. `uv run pytest analyzer/test_api.py -k corners -q`: 7 passed, 終了コード 0。
2. 壊すと落ちるか（関数名は brief と違い、synth-cube-photo4-2 は `test_corners_are_found_on_samples` の中）
   - 差し替えなし: 3 関数とも通る
   - `HINT_WEIGHT = 0`: `test_corners_are_found_on_samples` が `AssertionError: synth-cube-photo4-2` で落ちる。他の 2 つは通る
   - `locate = lambda img: None`: `test_corners_are_found_on_samples` が synth-cube-photo4-2 で落ちる。
     `test_corners_keep_the_fixed_ones_and_look_in_the_trimmed_part` も落ちる。traceback の行は
     `assert found is not None and _corner_error(found, truth, img.shape) < 0.036` で、メッセージ無し。この文は collected-sj1vrx の節にしか無い（画面の中での位置は行番号で確かめていない）。
3. check_corners（終了コード 0。出力は `check_corners-verify.txt`）
   - 集計: `within 3.6%: 50, further: 19, not found: 7`（hint-rf は 50 / 17 / 9）
   - 0.05 ポイントより動いたサンプル: collected-4b88u3 38.6% -> 44.7%、collected-mghnwm 見つからず -> 74.0%、collected-xqv7k9 見つからず -> 77.5%。他は 73 件が同じか 0.05 以内
   - 見つからなかった 2 件が、遠い位置で見つかる側に変わっている。四隅の順の直しの影響か、実害は未確認
4. `corners.locate`（photo2.jpg、2 回目以降 5 回）: 最小 0.022 秒、最大 0.023 秒
5. モデルが無いとき: `find_corners` は `cv2.error`（`Can't read ONNX file: /nonexistent/x.onnx`）を投げる。握りつぶさない

変更ファイル（git status）: README.md, TODO.md, analyzer/test_api.py, docs/corners.md, recognizer/README.md, recognizer/board.py, recognizer/corners.py, samples/CREDITS.md、新規 recognizer/corners_model.onnx, recognizer/train_corners.py, archives/agents/TODO-136/。
brief に範囲の指定は無く、指示との照合はしていない。
