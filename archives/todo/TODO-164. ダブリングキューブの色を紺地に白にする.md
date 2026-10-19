# TODO-164. ダブリングキューブの色を紺地に白にする

|      | main | 担当 |
|------|------|------|
| 見込み | Sonnet 5.5 / effort medium | implementer（Sonnet 5.5）+ reviewer + verifier（Sonnet 5.5） |
| 実施 | Opus 5.5 / effort 記載なし | implementer（teammate、Sonnet 5.5 / 記載なし）+ reviewer（teammate、記載なし）+ verifier（teammate、Sonnet 5.5 / 記載なし） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main（teammate の分を含む） | Opus 5.5 + Sonnet 5.5 | 記載なし | 216 | 39,066 | 325,688 | 6,361,133 | 100% |
| 合計 |  |  | 216 | 39,066 | 325,688 | 6,361,133 | 計 6,726,103 |

- teammate の分は main の行に含まれる（`token-usage.py` は teammate を分けて数えない）。モデル別の内訳は Opus 5.5 が 76%、Sonnet 5.5 が 24%
- 範囲は着手前の `--since '2026-10-20 01:50:00'` から作業の最後のコミット（`f6b027b`）まで。そのあとの確認の報告のコミットと、ローカルの確認は含まない

## きっかけ

盤面の画面のダブリングキューブの色が、盤の三角の色（`--tri-a` #c98f4a 薄茶、`--tri-b` #a33a2c 赤）と似ていて見分けにくかった。
見本の画像から「紺地に白」を利用者が選んだ（2026-10-20）。
実装の途中で、利用者がダブルの申し出中（テイクかパスを待つとき）は手番の矢印も描かないよう、追加で指示した。

## やったこと

- キューブの地を #f6eedb から #1f3f7a（紺）、縁と数字・Crawford の文字を #8b1a2b から #ffffff（白）にした（`analyzer/static/board-view.js` の `drawCube`、`analyzer/static/style.css` の `.cube-num` / `.cube-crawford`）。`rg -e f6eedb -e 8b1a2b analyzer/` に出たのはキューブだけで、ほかの色は変えていない
- ダブルの申し出中（`BgCube.offered(scene.cube)`）は `drawWay` を呼ばない（`board-view.js`。サイコロと同じ条件）。申し出たキューブの置き場所は矢印の定数（`WAY`）から出しているので、位置は変わらない
- `analyzer/README.md` とコメントを、申し出中は矢印が出ないと読めるように直した（reviewer の指摘）
- analyzer を 0.90.0 → 0.90.1（`analyzer/app.py` の `__version__`、`analyzer/static/app.js` の `APP_VERSION`）

## 確かめたこと

- `uv run pytest analyzer/test_pwa.py`: 34 件通った。GitHub Actions の `test` も通った
- verifier が Playwright で、真ん中・持ち主側・申し出中・Crawford の 4 つの状態を計算後の style で読み出した。地・縁・数字がすべて期待の色で、申し出中だけ矢印とサイコロが 0 個。食い違いなし（`archives/agents/TODO-164/verifier-report.md`）
- マージ後のローカルホスト（`bganalyzer.service`、analyzer 0.90.1、commit af6da8a）で、同じ `verify.py` を流し直した。4 つの状態とも rect の fill が rgb(31, 63, 122)、stroke と数字・Crawford の文字が rgb(255, 255, 255)。申し出中だけ矢印 0・サイコロ 0、ほかは矢印 1・サイコロ 2。期待どおり

## 分担の振り返り

- implementer: 色の変更と版の上げ、矢印の条件を実装した。reviewer の指摘で README とコメントを直した（文書の整合の取りこぼし）
- reviewer: 条件がサイコロと同じこと、キューブの位置の計算が描いた矢印に頼っていないことを確かめた。要修正は README（80〜81 行目）が「矢印はいつも出る」と読めること。検討は 2 つで、コメント 2 か所（264・285 行目）の直しと、条件を外しても落ちるテストが無いこと。後者は TODO-156 のサイコロの分岐と同じく、画面での確認に任せることにした
- verifier: 画面の読み出しに食い違いは無かった。live_view（9222）が開いていなかったので Chromium を直接起動した
- 見込みでは「挙動は変わらないので reviewer は要らない」だったが、矢印の条件を足して分岐が変わったので reviewer を足した。その reviewer が README の食い違いを見つけたので、足して正しかった
- 次に同じ規模（色の変更に小さな分岐が付く）をやるなら: 追加の指示で分岐が増えるかは立てる時点で分からないので、見込みは今のままでよい。README に動作の説明がある機能を変えるときは、implementer の依頼に「README の該当箇所を `rg` で探して直す」と最初から書き、reviewer の往復を 1 回減らす
- `board-view.js` の `BgBoardView.draw` を呼ぶテストは無く、描く分岐（TODO-156 のサイコロ、この項目の矢印）は CI で守られていない。画面で確かめる以外に守る手段が無い。テストを足すかは、分岐がもっと増えたときに別の項目で決める
