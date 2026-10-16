# verifier 報告: TODO-095・TODO-096（branch claude/todo-095-096、HEAD 56bef8c）

作業ツリーは変更なし（このレポートのみ追加）。コードは直していない。

## TODO-095（最近の写真を 100 件に）

手段: Playwright（chromium、390x844）。uvicorn を port 8765 で起動し、IndexedDB "bganalyzer" / "photos" に 12 件（時刻を 1 分ずつずらした JPEG サムネイル）を入れて再読み込み。終わったら PID（718906 / 718911）で停止し、port 8765 が閉じたことを確認。ページエラーは 0 件。

| 項目 | 結果（実測値） |
|---|---|
| 写真の画面 | `#photo` が表示、`#history` は非表示でない |
| li の数 | 12 |
| `#history-list` の clientHeight | 852px（= 10 行: 78px × 10 + 8px × 9） |
| scrollHeight | 1024px |
| overflow-y / max-height | auto / 852px |
| 10 個目の li の下端（リスト上端基準） | 852px（リストの下端と一致） |
| 11 個目の li の上端（ページ座標） | 1188.8px、リスト下端は 1181.8px（下に隠れている） |
| scrollTop を 10000 にしたあと | 172px（= 1024 − 852、最大）。11 個目は 1016.8px に来て見える範囲に入る |

判定: 一致。10 件分の高さで止まり、中をスクロールできる。

## TODO-096（振る前のダブル）

1. `uv run pytest -q analyzer/test_api.py -k cube`: 8 passed, 39 deselected, 終了コード 0。
2. `uv run pytest -q analyzer/test_pwa.py`: 25 passed, 終了コード 0。
3. `analysis.analyze` の直接呼び出し（局面は test_api.py の `_race({1:3,2:3,3:3,4:2}, {6:3,7:3,8:3,9:2})`、white、plies=0）:
   - (a) `dice=(3,1)`: `cube` = `{"question": "double", "doubler": "white", "taker": "black", "double": true, "take": false, "rolled": true, "proper": "Double, pass", ...}`、`moves` は 5 件（先頭 `4/off`）。一致。
   - (b) 同じ局面で `cube_value=2, cube_owner="black", dice=(3,1)`: `cube` = null、`moves` あり。一致。
   - 注: 実行は `if __name__ == "__main__"` で囲んだスクリプト（engine のプロセスプールに必要）。出力は最後まで出ており、a.json も書けたので最後まで走っている。終了コードは pipe の都合で取り直せていない。
4. `analyzer/static/result.js`（node で require、(a) の結果を入力）:
   - `html`: 「キューブ（振る前）」の見出しが位置 150、「最善手」の見出しが位置 452。キューブが最善手より前。一致。
     - 答え: 「白の人は振る前に **ダブルすべきだった**」、「ダブルされたら、黒の人はパス。」
   - `speechText`: 「振る前に白の人はダブルすべきでした。ダブルされたら黒の人はパスです。白の人、ダイス 3 1の最善手は、4から上がり。…」。先頭は「振る前に」（index 0）。一致。
   - 比較用に cube と moves を外すと「振ったのは白の人です。…」になり、通常の読み上げは壊れていない。

## 食い違い

なし。

## 確かめられなかったこと・判断が要ること

- test_api.py / test_pwa.py の全体は流していない（指示どおり。CI の範囲）。
- Pi と他のサンプルの精度は見ていない（指示どおり）。
- 「分岐を壊して落ちるか」は今回の依頼に含まれていないので確かめていない。
- Playwright の 12 件はシード用の仮の JPEG で、実写真の表示は見ていない（高さとスクロールの確認には影響しない）。
