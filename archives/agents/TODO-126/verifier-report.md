# TODO-126 verifier 報告

HEAD 0e21535、analyzer 0.70.0 / recognizer 0.24.0。127.0.0.1:8126 で起動、live_view のブラウザ（CDP 9222）で操作。サンプルは screen1（truth: home=left, bottom_colour=1）。スクリプト: `archives/agents/TODO-126/verify.py`（終了コード 0、13 項目 OK）。uvicorn は停止済み。

1. OK 四隅の画面: near-right → homePick=right, bottomColour=1。far-left → left, 0。「自動」→ homePick="auto", bottomColour=0 のまま、図に path・polygon なし。点は奥の行 2 つが fill-opacity 0.4、手前の行 2 つが 1。
2. OK truth どおり near-left を押して読み取り → `#home-svg` の矢印の終点 near-left、home=left、bottomColour=1。points は truth と一致 `[-1,0,0,0,-1,5,0,3,0,0,0,-4,5,0,-1,0,-3,0,-5,0,0,0,0,2]`、bar 0/0。
3. OK 奥の隅（far-left）→ bottomColour=0、points 全符号反転、bar は入れ替え（0/0 なので値の変化は見えず）、home=left 不変。続けて far-right → home=right、bottomColour=0 のまま。盤は各半分の中で i→11-i（12 以上は 35-i）に並べ替わっていて、非ゼロ 10 点すべて手で突き合わせて一致（左右の鏡写し）。bar は不変。
4. OK `#swap-colours` は DOM に無い。
5. OK 矢印の終点（path の d の最後の `H`、y が 40 より下か上か・x が 60 より左か右か）: 四隅の画面 near-right（`M96,20 H44 A… 44,60 H86`）、far-left（`M24,60 H76 A… 76,20 H34`）、盤面の画面 near-left・far-left・far-right、すべて選んだ隅と一致。`#home-svg` / `#home-pick` の要素スクリーンショット（shot-*.png）で、図が欠けず重ならず、矢じりが選んだ隅を指していることを目視で確認（far-left、far-right、自動で矢印なし）。
6. OK 3 の後（far-right 状態）で「解析する」→ 結果が出た、pageerror・dialog なし。
7. 一部流せた: `BG_URL=http://127.0.0.1:8126/ BG_CDP=http://127.0.0.1:9222 uv run … tools/pi_ui_check.py` → double・speech・export・export-denied は OK、collect が FAIL（`TimeoutError: Page.click: Timeout 30000ms exceeded.`）。

## 食い違い・注意（実害は未確認）

- collect の FAIL: このサーバーは `BG_SAMPLES_DIR` を設定しておらず、`/version` が `samples:false`。保存の UI が出ないためのタイムアウトの可能性があるが、これは推定で、確かめていない。TODO-126 の変更との関係も未確認。
- 盤面の画面で反転した points に JS の `-0` が混ざる（例 `[1,-0,-0,-0,1,-5,…]`。0 の符号を反転した結果）。表示や解析には支障が出ていない（6 は通った）。送信 JSON では `0` になる見込みだが、確かめていない。
- shot-board-0.png は、最初の要素スクリーンショットがスクロール中に撮れて `#home-svg` でなく盤面の一部が写った。図は shot-board-1/2 と corners 側で確認した。
- 確かめていないこと: 手前・奥の各隅すべて（代表のみ）、スマホ実機。
