# TODO-068 reviewer への依頼

## 目的

四隅の画面で「検出 → ユーザーが直す → もう一度検出」を繰り返せるようにした変更が、正しく、規約に合っているかを見る。

## 対象

`git diff main -- recognizer/corners.py recognizer/check_corners.py analyzer/ ` の範囲（コミット前の作業ツリー。`git diff` で見る）。
背景は `TODO.md` の TODO-068 の節、`archives/agents/TODO-068/README.md`、依頼の中身は `archives/agents/TODO-068/implementer-request.md`。

## 見てほしいこと

- `corners.py`: `fixed` を渡したとき、固定した隅から `NEAR` より離れた候補を捨て、残りに固定した隅を入れて（`pin`）点数を付ける流れ。
  `_move_in` のあとに `pin` し直すこと、`crop` の切り出しと座標の戻し（`progress` の座標も）、`TRIMMED` の使い方。
  **何も渡さないときの答えが前とビット単位で同じか**（`trace_cpu.py check` は一致した。重複の除き方 `looked` が既定の流れの順位を変えないかも読む）
- CLAUDE.md の「精度の確認」: 読み取りに float の OpenCV や NumPy の `linalg` などを入れていないか
- `/find-corners` の `fixed`・`crop` の受け取りと 422 の扱い（`/analyze-photo` の `corners` と揃っているか）
- PWA: 固定の印（どの隅をユーザーが置いたか）の付け方と消し方、トリミングの表示（拡大・`toImage` の範囲）、もう一度検出の結果の当て方
  （固定していない隅だけを置き換える、見つからないときの扱い、検出中にユーザーが動かしたら捨てる）、途中経過の重ね描きとの関係、新しい写真で状態が消えること
- 版（analyzer 0.44.0 と `APP_VERSION`、`sw.js` の `CACHE`、recognizer 0.22.0）

## 見なくてよいこと

- 四隅の当たり具合の測り直し（値は README にある）。三角形の点数（`_structure`）そのものの良し悪し
- 文書の文体

## 報告

`archives/agents/TODO-068/reviewer-report.md` に、問題ごとに「場所・何が起きるか・根拠」を書く。問題の無い観点は 1 行で済ませる。
コードは直さない。原因の切り分けや、境界線上の判断はしない（「実害は未確認」と添えて報告だけ）。
返事は「終わったか・報告ファイルのパス・判断が要る点」だけにする。

## 追記（implementer のあと）

implementer の報告は `archives/agents/TODO-068/implementer-report.md`。報告の「判断が要る点」（固定した隅が囲んだ範囲の外にある）は、
main が `analyzer/static/app.js` の `onTrim` で「範囲の外にある隅の固定を外す」ことにした。これも見る。
