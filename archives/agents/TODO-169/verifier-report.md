# TODO-169 verifier の報告

worktree `impl-169`（HEAD 63ed6b8）で `uvicorn --port 8023` を起動し、`POST /analyze` の応答（初期局面 `4HPwATDgc/ABMA`、white 番、
ダイスあり 3-1 とダイスなし）を、サーバーが配る PWA のページ（Playwright・/usr/bin/chromium・390×844）で読み込んだ
`BgResult.html(r, dice)` に渡し、`evaluate` で見出しの文字列・`getBoundingClientRect` をまとめて読んだ。各 1 回。
写真から結果の画面までの操作はしていない（TODO-167 の確認と同じ方法）。サーバーは止めた（8023 に残りなし）。
測るスクリプト: `archives/agents/TODO-169/measure.py`。画像: `archives/agents/TODO-169/result-dice.png`（ダイスありの結果の部分）。

## ダイスあり（3-1）
- 期待どおり。`h2` は「最善手（白・ダイス 3-1）」。`.result h3` は 2 つで、順に「この目で動かした後」「ダイスを振る前」。
- 期待どおり。「この目で動かした後」の直後の要素は `OL.moves`、「ダイスを振る前」の直後は `TABLE`（勝率の表）。
- 期待どおり。重なり・欠けなし。幅 364、文字 14px、色 rgb(102,102,102)、`scrollWidth` = `clientWidth`（364）、横スクロールなし（`docW` 390）。
  縦の位置（y, 高さ）: 前の `p` 116+24 → h3 156+21（〜177）→ `ol` 181。 `p` 354+39（〜393）→ h3 406+21（〜427）→ `table` 435。すべて間が空いていて重ならない。
- 画像を見て、見出しは灰色の小さい太字で、一覧・表と重なっておらず、文字も欠けていない。

## ダイスなし
- 期待どおり。`h2` は「キューブ」。`.result h3` は「ダイスを振る前」の 1 つだけ（「この目で動かした後」は出ない）。直後は `TABLE`。
  位置 y 456.5、高さ 21、前の `p`（424+19.5）と表（485.5）の間で重ならない。`docW` 390。

## 期待と違った点
なし。

## 補足（境界線上のものは報告だけ。実害は未確認）
- 見出しの見た目（灰色・14px）のデザインの良し悪しは評価していない。
- キューブの判断だけの局面（ダイスなし・`h2` が「キューブ」）でも「ダイスを振る前」が出る。指示どおり。
- `git diff origin/main` の変更ファイルは TODO.md・analyzer（README・app・static/app.js・result.js・style.css・test_pwa.py）・archives/agents/TODO-169/implementer-report.md で、指示の範囲内。
