# TODO-126. ホームの位置と手前の駒の色を、U 字の矢印の隅をタップして決める

| | main | 担当 |
|---|---|---|
| 見込み | Opus 5.5 / effort high | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Sonnet 5.5 / medium） |
| 実施 | Opus 5.5 / effort high | main（実装）+ reviewer（Opus 5.5 / high、2 回）+ verifier（Sonnet 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | high | 70 | 21,764 | 78,838 | 2,834,639 | 72% |
| reviewer | Opus 5.5 | high | 42 | 183 | 75,909 | 1,043,810 | 28% |
| 合計 |  |  | 112 | 21,947 | 154,747 | 3,878,449 | 計 4,055,255 |

- verifier は定義のモデルが haiku。画面を操作して値を読む確認なので Sonnet 5.5 に上書きした（effort は定義の medium）
- verifier は終点のコミット（0e21535）より後に動いたので表に入っていない。完了の通知では 49,917 トークン
- reviewer の effort は Agent ツールで high を指定した（定義も high）

## きっかけ

2026-10-18 ユーザーの指示。四隅の画面の「手前のホーム（自動・左・右）」「手前の駒の色（暗い方・明るい方）」と、盤面の画面の「白のホーム（左・右）」をボタンで選んでいた。

## やったこと

- 両方の画面のボタンを、小さな盤の図（明るい駒の進み方の U 字の矢印と四隅の点）に置き換えた。タップした隅が明るい駒のホームで、行が手前の駒の色、列がホームの左右（`analyzer/static/app.js` の `drawHomePick`）
- 四隅の画面は「自動」を残した。自動のときは矢印を描かず、手前か奥の行の 2 つの点を薄く光らせて手前の駒の色を示す（2026-10-18 ユーザーが決めた）
- 盤面の画面で行を変えると、駒の持ち主を入れ替える（写真の明るい駒は明るいまま。2026-10-18 ユーザーが決めた）。同じ処理になった「色を入れ替え」ボタンは消した（同）
- `tools/pi_ui_check.py`・`tools/ui_snapshot.py`、analyzer と recognizer の README を新しい図に合わせた
- analyzer 0.69.2 → 0.70.0

## 確かめたこと

- reviewer: 隅と home・bottomColour の対応、矢印の向き（4 隅とも drawWay と一致）、盤面の画面での入れ替えと鏡写しの組み合わせ。報告は `archives/agents/TODO-126/reviewer-report.md`
- verifier: ブランチのサーバーを live_view の窓で操作し、両方の画面の隅・自動・読み取り・解析が通った。報告は `archives/agents/TODO-126/verifier-report.md`。pi_ui_check の collect はサーバーが samples を保存しない設定だったため落ちた（この変更とは関係ない）
- ユーザーがマージ後にスマホで確かめた

## 分担の振り返り

- reviewer は 1 回目で、ui_snapshot.py が消えた seg を押すこと、README が古いボタンを説明していることを見つけた。加えて「自動のときに色が見えないまま残る」「色を入れ替えボタンが重複する」を挙げ、ユーザーの判断で仕様が足された。2 回目は README の 1 行だけ
- verifier は食い違いを見つけなかった。`-0` が混ざること（前からある swapColours のもの）を報告した
- 見込みとの差は reviewer が 2 回になったこと。1 回目の指摘で挙動を足したため。次に同じ規模なら、ボタンを置き換える項目では「置き換えたあと残る値（今回の自動のときの色）」と「重複するボタン」を項目を立てるときに聞いておけば、reviewer は 1 回で済む
