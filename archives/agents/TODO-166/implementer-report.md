# TODO-166 implementer の報告

## 変更点
- `analyzer/static/result.js`
  - `cubeLabel`（新設）: 「ノーダブル／テイク」「ダブル／パス」「トゥーグッド／パス」「ノーリダブル／テイク」「オプショナルダブル／テイク」。答えの行（3 通り）に `（…）` で添え、読み上げでは先に「ノーダブル、テイク。」と読む（読まないことにしている「してもしなくてもよい」の局面は今までどおり読まない）
  - 注記: `gnubg ${plies}-ply（XG の ${plies+1}-ply 相当）`
  - `distanceHtml`: 案は下。gnubg の `(25.6%)` を使う「遠さ」と一歩手前などの語を廃止
  - `moveToSpeech`: 途中のヒット `24/18*/13` を「にじゅうよんからじゅうはちでヒットして、じゅうさんへ」と読む（最後の点のヒット・`(2)` の枚数も確認）
- `analyzer/analysis.py`: `cube_label_ja` を足し、`cube_summary_ja`（summary）の頭に「ノーダブル／テイク: 」を付ける
- `analyzer/static/app.js`: `APP_VERSION` 0.92.0、読み込み中の文を「3-ply で解析しています」に
- `analyzer/app.py`: `__version__` 0.92.0
- `analyzer/README.md`: 結果の画面の説明（定型の語・差・2-ply）と「手読み」の用語
- `analyzer/test_pwa.py`・`analyzer/test_api.py`: 上の各表記（定型の語の 5 通り、2-ply、ヒットの読み、差の符号と値、summary）
- `TODO.md`: TODO-166 の実装 4 項目にチェック

## 「ダブルまでの遠さ」の案（reviewer 向け）
`ダブルした場合のエクイティ差 -0.100（ダブルとノーダブルの差。マイナスはダブルすると損）`
- 値 = min(ダブル・テイク, ダブル・パス) − ノーダブル（ダブルする人から見て）。相手は自分に良い方を選ぶので低い方を取る。0 に近いほどダブルに近い
- マッチでは表と同じ MWC の差を `%` で（`-1.42%` の形、2 桁）。マネーはエクイティ 3 桁
- gnubg の `(25.6%)` は使わない（注記の gnubg 原文には残る）。ギャモン狙いでも同じ式
- 前は gnubg が % を出したときだけだったが、今は表の 3 つの数から常に出す（ダブルが正しい局面でもプラスで出る）。値が数でなければ出さない
- 迷う点: 「エクイティ差」の語、プラスのときの添え方（今はマイナスの説明だけ）。XG の表示に合わせるなら変えるので、reviewer の意見を聞きたい

## 検証
- `uv run pytest analyzer/test_pwa.py` 35 passed
- `uv run pytest analyzer/test_api.py` 51 passed、1 failed（`test_version_reports_both_parts_and_commit`。worktree で落ちると分かっているもの）
- node で result.js を直接読み、`24/18*/13` 系の 3 通りを test_pwa に入れた

## 残る懸念
- 読み上げの「、」は TTS の間のとり方に任せる。ローカルの確認で聞いてもらう
- 範囲外: `README.md`（トップ）に「手読み」は無い
