# TODO-125 verifier への依頼

目的: ブランチ `claude/todo-125-count-mark`（コミット 23d510f）の駒の数の警告（`#count-mark`）の変更が TODO.md の TODO-125 のとおりか、実際の画面で確かめる。コードは直さない。境界線上の判断は報告だけ。

## 期待
1. `#count-mark` が盤面図（`#board-svg` の `.board-wrap`）のすぐ上に出る。「元の写真を並べる」を入れたときは、写真と盤面の間（2 列なら盤面の列の上）
2. 15 個より多い側の文字は赤（`.many`、rgb(198, 40, 40)）、少ない側は濃いめの黄色（`.few`、rgb(201, 154, 0)）。白・黒で別々の色になる
3. 「盤に駒がありません」は黄色
4. 少ない側を出すのは写真から読んだときだけ（手で作った盤では 15 未満でも出ない。分岐は変えていない）
5. `/version` と app.js の `APP_VERSION` が 0.69.2

## やり方
- サーバーは常駐の bganalyzer.service（ポート 8000）を触らず、別に起動する:
  `uv run uvicorn app:app --app-dir analyzer --host 127.0.0.1 --port 8001`（終わったら止める。pkill は使わず PID で）
- Playwright（`uv run -q --no-project --with playwright python ...`）、スマホの大きさ（390x844）で `http://127.0.0.1:8001/` を開く。手順は `tools/pi_ui_check.py` を参考に `samples/` の写真を 1 枚読ませる
- 盤で駒を足して 1 色を 16 個以上、もう 1 色を引いて 14 個以下にし、`evaluate` で `#count-mark` の各 span の textContent と `getComputedStyle(...).color` をまとめて読む。`#count-mark` と `.board-wrap`（盤面図）・`#photo-wrap` の `getBoundingClientRect().top` も読み、並びを数値で示す
- 「元の写真を並べる」を入れた状態でも位置を 1 回読む（幅 390 と 1300 の 2 つ）
- 「盤に駒がありません」は盤を全部空にして 1 回だけ
- 各確認は 1 回ずつでよい。全サンプル・テスト全体は流さない（CI が見る）

## 報告
`archives/agents/TODO-125/verifier-report.md` に、一致したものは 1 行、食い違いは測った値つきで詳しく。返事は「終わったか・報告のパス・判断が要る点」だけ。
