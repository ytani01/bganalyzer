# TODO-116. 盤面に誤りがあるとき「解析する」をグレーアウトし、理由を出す

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort high | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |
| 実施 | Opus 5.5 / effort high | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | high | 210 | 46,439 | 211,053 | 11,258,617 | 89% |
| reviewer | Opus 5.5 | high | 44 | 200 | 106,506 | 794,459 | 7% |
| verifier | Haiku 5.5 | medium | 30 | 5,454 | 68,857 | 377,796 | 4% |
| 合計 |  |  | 284 | 52,093 | 386,416 | 12,430,872 | 計 12,869,665 |

- reviewer・verifier とも定義（`~/.claude/agents/`）のモデルと effort のまま。Agent ツールでも同じ値を渡した
- 範囲は項目を立てたコミットからなので、main には立てたときのやり取りも入っている

## きっかけ

「解析する」を押したときに `BgBoard.errors`（1 色 16 個以上、盤に駒が無い）とクロフォードのキューブ（`crawfordCube`）を調べ、`alert` で止めていた。
押す前に分かるように、盤面や設定が変わるたびに調べ、誤りがあればグレーアウトして理由を出すことにした（2026-10-17 ユーザーが決めた）。

## やったこと

- `analyzer/static/app.js`: `analyzeErrors` を足し、`[s.step, s.board, s.match.crawford, s.cube.at, s.bottomColour]` が変わるたびに `#analyze` の `disabled` と `#analyze-why` の理由を描く part を足した。
  `BgResult.setNames` を呼ぶ part より後ろに置いた（理由の「白／黒」が手前の色に追いつくように）。`crawfordCube`・`CRAWFORD_CUBE` は前へ移した。`analyze()` の `alert` はやめ、誤りがあれば何もせず戻る
- `analyzer/static/index.html`・`style.css`: 下のバーの「解析後、自動で読み上げる」（TODO-115）の上に `#analyze-why` を置いた
- `analyzer/README.md`: グレーアウトと理由のことを書き足し、クロフォードの説明を直した
- `analyzer/test_pwa.py`: alert の文字列を見ていたところを、新しい実装の文字列に合わせた
- analyzer の版を 0.66.0 に（`APP_VERSION` も）

## 確かめたこと

- verifier がブランチをローカルに起動し、Playwright で操作して確かめた（[報告](../agents/TODO-116/verifier-report.md)）。駒 16 個・駒が無い・クロフォードのキューブのそれぞれで disabled と理由が出て、元に戻す／初期配置／キューブを中央にすると押せるように戻った。結果の画面では出ない
- 手前の色の名前: 盤面の画面の「色を入れ替え」は駒と手前の色を一緒に入れ替えるので、16 個の明るい駒は「白」のままが正しい。part が名前の設定より前にあると「黒」になるところで、「白」のままだった
- マージ後、ローカルの `bganalyzer.service`（0.66.0）に同じ操作を流し、同じ結果だった
- `uv run pytest analyzer/test_pwa.py` は 25 件通った。CI の test も通った

## 分担の振り返り

- reviewer: part の key に `s.bottomColour` が無く、`BgResult.setNames` の part より前にあるため、手前の色を切り替えると理由の「白／黒」が古いまま残ることを見つけた。実装の段階では気づいていなかった
- verifier: 指示した 6 点のうち 5 点を値つきで確かめた。手前の色の切り替えは写真の画面にしか無く確かめられないと報告した。「色を入れ替え」の結果で足りると main が判断した
- 見込みどおりの編成で、食い違いは無かった。main の cache_read が大きいのは、CI の待ちとローカルの確認を main がしたため。次に同じ規模なら同じ編成で、verifier の依頼には「その操作がどの画面にあるか」を先に調べて書く（今回は手前の色の切り替えのある画面を書き違えた）
