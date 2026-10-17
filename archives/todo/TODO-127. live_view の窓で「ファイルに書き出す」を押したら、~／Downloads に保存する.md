# TODO-127. live_view の窓で「ファイルに書き出す」を押したら、~/Downloads に保存する

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort medium | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Sonnet 5.5 / medium） |
| 実施 | Opus 5.5 / effort medium | main（実装）+ reviewer（Opus 5.5 / high）+ verifier（Sonnet 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | medium | 106 | 17,850 | 110,918 | 3,802,376 | 84% |
| reviewer | Opus 5.5 | high | 24 | 125 | 50,772 | 417,984 | 10% |
| verifier | Sonnet 5.5 | medium | 22 | 154 | 56,485 | 245,518 | 6% |
| 合計 |  |  | 152 | 18,129 | 218,175 | 4,465,878 | 計 4,702,334 |

- verifier は定義のモデルが haiku。Playwright で窓を操作する実測なので、見込みどおり Sonnet 5.5 に上書きした
- main の分には、項目を立てたセッション（始点のコミットの前後）のやり取りも含まれる

## きっかけ

2026-10-18 ユーザーの指示。`tools/live_view.py` の窓は Playwright が開いたもので、ダウンロードは Playwright の一時フォルダに置かれ、窓を閉じると消える。

## やったこと

- `tools/live_view.py`: `context.on("page", ...)` で窓の page に `download` の受け口を付け、`~/Downloads` に `save_as` する。同じ名前があれば `名前 (1).拡張子` のように変えて上書きしない。保存に失敗したときは `not saved:` を表示して live_view を続ける（失敗が次の待ちで投げ直され、窓を閉じたのと同じに扱われて黙って終わるのを防ぐ。reviewer の指摘）
- `CLAUDE.md` のコマンドの行と `docs/raspi.md` の live_view の説明に保存先を書き足した
- アプリ（analyzer）は変えていないので版は上げていない

## 確かめたこと

- verifier が新しいコードで live_view を起動し、CDP でつないで写真を 1 枚読み、「ファイルに書き出す」を 1 回押した。`~/Downloads` に `user-20261018-0136.png` と `user-20261018-0136.truth.json` が増え、live_view の出力に `saved:` が 2 行出た（`archives/agents/TODO-127/verifier-report.md`）
- reviewer が playwright 1.62.0 のソースで、`new_page()` の page にも受け口が付くこと、ハンドラーの中で `save_as` を呼べること、続く 2 つのダウンロードを取りこぼさないことを確かめた（`archives/agents/TODO-127/reviewer-report.md`）

reviewer が挙げた次の 2 つは直していない。

- 同じ分に 2 回書き出すと 2 回目に `(1)` が付き、`.truth.json` の `image` が 1 回目の写真を指す。ふつうの Chromium の保存でも同じで、この変更で増えた問題ではない
- 同じ名前のダウンロードが同時に来ると上書きしうる。「ファイルに書き出す」は 2 つの名前が違うので起きない

## 分担の振り返り

- reviewer は、保存の失敗で live_view が黙って終わる経路を見つけた（実装に反映）。実行せずソースを読んで受け方の正しさも確かめた
- verifier は 1 回の書き出しで 2 ファイルが残ることを実測した。食い違いは無し
- 見込みと実施は同じ。次に同じ規模（16 行ほどのツールの直し）なら同じ組み方でよいが、reviewer の依頼から「Playwright の仕様の確かめ」を外せば、verifier の実測で分かる分だけ reviewer が軽くなる
