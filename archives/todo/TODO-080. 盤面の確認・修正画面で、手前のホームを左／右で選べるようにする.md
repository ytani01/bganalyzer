# TODO-080. 盤面の確認・修正画面で、手前のホームを左／右で選べるようにする

| | main | 担当 |
|---|---|---|
| 見込み | Opus 5.5 / effort medium | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Sonnet 5.5 / medium） |
| 実施 | Opus 5.5 / effort medium | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Sonnet 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | medium | 38 | 8,490 | 21,992 | 1,340,204 | 66% |
| reviewer | Opus 5.5 | high | 22 | 100 | 50,806 | 391,336 | 21% |
| verifier | Sonnet 5.5 | medium | 18 | 143 | 34,272 | 229,941 | 13% |
| 合計 |  |  | 78 | 8,733 | 107,070 | 1,961,481 | 計 2,077,362 |

- verifier は定義のモデルが haiku。ブラウザでの実測なので、見込みどおり Sonnet 5.5 に上書きした（effort は定義の medium）
- サブエージェントの分は少なめに出ている（token-usage.py の制約）

## きっかけ

ユーザーから「盤面の確認・修正画面でもゴールの方向を修正できるようにして」と頼まれた。
画面3には「左右を入れ替える」ボタンがすでにあったが、今どちら向きかが見えず、見つけにくかった。
画面2と同じ「手前のホーム（上がる側）」の左／右の切り替えにすることをユーザーが選んだ（2026-10-16）。

## やったこと

- `analyzer/static/index.html`: `#flip-home` をやめ、`.seg[data-name="home"]`（左／右）を `#home-note` の上に置いた。「自動」は出さない
- `analyzer/static/app.js`: `setHome(v)` を足した（同じ側なら何もしない。反対なら前のボタンと同じく `BgBoard.mirror` と `home` の切り替え）。
  セグメントの表示に `home` を足し、`#home-note` の「逆なら…」の文言を「手前のホーム」で選び直す形にした
- analyzer の版を 0.46.0 → 0.47.0（`APP_VERSION` も）
- `analyzer/README.md`・`recognizer/README.md`・`tools/ui_snapshot.py` の、前のボタンを指していた所を直した

## 確かめたこと

- reviewer: 要修正なし。画面2の `homePick` と画面3の選択が食い違って見えることがある、と指摘（下の「残ること」）。README の言い回しの残りは直した
- verifier（Chromium 390x844、手入力の初期配置）: 最初は右が選ばれ、同じ側を押しても `#board-svg` は変わらず、左を押すとポイント番号の付き方が逆になり、右に戻すと最初と完全に一致した。
  `uv run pytest analyzer/test_pwa.py` は 18 passed、`ui_snapshot.py record ... manual` は "home left" の段まで通った
- 写真から読んだときの `#home-note` の文言は画面では見ていない（文字列の置き換えだけ）

## 残ること

- 画面2の「自動／左／右」（次に読むときの指定）と、画面3の左／右（今の盤面の向き）は連動しない。
  画面3で選び直しても画面2は変わらない。役割が違うので揃えなかった（main の判断。気になるなら別の項目にする）

## 分担の振り返り

- reviewer は画面2と画面3の食い違いと README の言い回しの残りを見つけた。verifier は食い違いを見つけなかったが、初期配置が左右対称なので駒の見た目では鏡写しを確かめられないことを報告した
- 見込みどおりの編成で動いた
- 次に同じ規模（画面の部品の置き換え 1 つ）なら同じ組み方でよい。verifier には左右非対称な盤面（駒を 1 つ動かしてから）で確かめるよう依頼に書く
