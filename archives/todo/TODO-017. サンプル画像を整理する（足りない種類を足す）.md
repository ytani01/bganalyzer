# TODO-017. サンプル画像を整理する（足りない種類を足す）

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort medium（画像探しと正解の読み取り） | verifier（Sonnet 5.5 に上書き / medium。正解・出典・顔の有無の突き合わせ） |
| 実施 | Opus 5.5 / effort medium | verifier（Sonnet 5.5 に上書き / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | medium | 100 | 35,858 | 110,036 | 6,662,658 | 93% |
| verifier | Sonnet 5.5 | medium | 24 | 5,632 | 65,148 | 441,101 | 7% |
| 合計 |  |  | 124 | 41,490 | 175,184 | 7,103,759 | 計 7,320,557 |

- verifier は定義のモデルが haiku。突き合わせる対象が 72 ポイントあるので Sonnet 5.5 に上書きした

## きっかけ

サンプルは同じ撮影者・同じ初期配置の Tavli 7 枚に偏り、途中局面の実物写真・斜め撮影・盤上のダイスの写真が少なかった。
当初は TODO-015 として立てたが、完了済みの TODO-015（ダイス）と番号がぶつかったので付け直した。
Tavli 7 枚は消さないと ai1 が決めた（2026-10-13）。

## やったこと

- Wikimedia Commons の Backgammon カテゴリから、顔が写っておらず CC BY / CC BY-SA で、盤全体が見える写真を 3 枚足した
  （長辺 1920px 版）。正解は目で読んだ。
  - `commons-case-dice`: ほぼ真上、右半分が影、盤上にダイス 5-3
  - `commons-nardy-midgame`: やや斜め、途中局面（ロングナルディ。ホームは駒の配置からの推測に合わせて右に仮に決めた）
  - `commons-rollup-oblique`: 強い斜め、初期配置、ダイス 2 組とキューブ
- `samples/CREDITS.md` に出典、`recognizer/README.md` に精度・ダイス・四隅の推定の結果を足した
- `analyzer/test_api.py` の `test_steep_photo_is_flagged` を、斜めの 2 枚（42.6°・55.5°）は警告され、ほかはされない、に変えた

## 確かめたこと

- 認識は 72 ポイント中 49（18・18・13）。外した原因は README に書いた
- Raspberry Pi（aarch64）では、同じ OpenCV 5.0.0 でも既存の leather-cups が 9（README は 14）、photo2 が 22（23）になる。
  ダイスを入れる前のコミットでも同じ値なので後退ではない。README に書いた
- pytest は常駐用のイメージに pytest と httpx を足して Pi で実行し、git の無いコンテナで動かない
  `test_version_reports_both_parts_and_commit` 以外は通った（23 passed）。GitHub Actions の `test` はまだ
- verifier が正解・ダイス・出典・大きさ・顔の有無・evaluate の値を突き合わせ、README の「10 か所」が 9 か所の誤りだったのを見つけた（直した）

## 分担の振り返り

- verifier は README の数え違い 1 か所を見つけた。正解の読み違いは無かった
- 見込みどおりの編成だった。トークンの 93% は main の cache_read で、候補の一覧画像や切り出しを何度も見たことによる
- 次に同じ規模でサンプルを足すなら、候補の一覧画像を 1 回で作る（Commons の API は間隔を空けないと応答が空になるので、最初から sleep を入れる）
