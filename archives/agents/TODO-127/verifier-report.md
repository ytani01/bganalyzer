# TODO-127 verifier 報告

結果: 通った（1 回の確認のみ。名前の重複・テストは対象外）。

## 手順と結果
- 古い live_view（PID 1228204 / 1228215）を kill、新しいコードで再起動（現在 PID 1233101 / 1233111、起動したまま）。
- Playwright `connect_over_cdp("http://127.0.0.1:9222")` で `contexts[0].pages[0]`（url http://127.0.0.1:8000/）を操作。
  samples/screen1 を読み込み、四隅→盤面（`#recognize`）まで進めて `#export-sample` を 1 回押した。
  （collect は localStorage で off にしたので collected/ には増えていない）
- ~/Downloads は 107 → 109 件。増えたのは次の 2 つ（消していない）:
  - /home/ytani/Downloads/user-20261018-0136.png
  - /home/ytani/Downloads/user-20261018-0136.truth.json
- live_view の出力:
  ```
  http://127.0.0.1:8000/ at ec82fca
  saved: /home/ytani/Downloads/user-20261018-0136.truth.json
  saved: /home/ytani/Downloads/user-20261018-0136.png
  ```
  `saved:` が 2 行。`not saved:` は無し。

## 差分の範囲
`git diff main --stat`: CLAUDE.md, TODO.md, docs/raspi.md, tools/live_view.py（+ 未追跡の archives/agents/TODO-127/）。tools/live_view.py 以外は文書。コードは直していない。

## 確かめていないこと
- 保存したファイルの中身（画像が元写真と同一か、JSON の内容）は見ていない。
- 判断が要る点なし。
