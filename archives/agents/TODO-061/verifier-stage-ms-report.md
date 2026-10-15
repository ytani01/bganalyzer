# verifier 報告（TODO-061 STAGE_MS 0.5 秒、91654d4）

- 差分の範囲: TODO.md, analyzer/README.md, app.py, static/app.js, static/scan.js, test_photo_view.py のみ。指示と一致。
- 1. node で読み出し: STAGE_MS = {"edges":500,"uprights":500,"candidates":500,"corners":500,"fit":500,"board":500,"tips":500,"checkers":500,"counts":500,"dice":500,"cube":500}、DEFAULT_STAGE_MS = 500。全部 500。
- 2. `pytest analyzer/test_photo_view.py -q -k "overlays or stage_times"`: 変更なしで 2 passed。edges を 1000 にすると 2 failed (test_stage_times_are_in_one_table, test_overlays_show_stages_in_turn_with_only_numbers)。`git checkout` で戻し、git status は空。
- 3. __version__ = "0.43.0"（app.py:31）、APP_VERSION = "0.43.0"（app.js:14）。一致。README:81 は「どの段階も 500 ミリ秒」で実装と一致。
- 4. 食い違う記述なし。scan.js の残りの 500/1000/1500 は別の用途（アニメーションの時間など）。docs/PI_CHECKS.md に該当の記述なし。
- 確かめなかった: 画面の操作、全体の pytest（指示により）。
