# TODO-130. Pixel で「写真を選ぶ」が複数選択の画面になる（対応しない）

| | main | 担当 |
|---|---|---|
| 見込み | Opus 5.5 / effort medium | main（調査・実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |
| 実施 | Opus 5.5 / effort medium | main のみ |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | medium | 34 | 6,663 | 53,874 | 1,114,004 | 100% |
| 合計 |  |  | 34 | 6,663 | 53,874 | 1,114,004 | 計 1,174,575 |

- コードを変えなかったので reviewer・verifier は立てなかった

## きっかけ

スマホ（Pixel）で「写真を選ぶ」を押すと、写真を複数選べる画面が出る（2026-10-18 ユーザー）。
`analyzer/static/index.html` の `<input id="file" type="file" accept="image/*">` に `multiple` は付いていない。

## やらないと決めた理由

- Chrome の `ui/android/java/src/org/chromium/ui/base/SelectFileDialog.java` は、`multiple` の無い input では
  `showPhotoPicker` に `allowMultiple=false` を渡している。ページ側で 1 枚に絞る指定はもう出ていて、ほかに付けられる属性も無い。
  Chrome・Android の不具合の報告も見つからなかった
- Pixel の画面は Google フォトの写真選択の画面だった。写真を押すとチェックが付き、下に「1・プレビュー・完了」が出る。
  別の写真を押すとチェックが移り、数は 1 のまま（2026-10-18 ユーザーが確かめた）。つまり 1 枚選択の画面で、
  「完了」を押す手間があるだけ。これは Android・Google フォトの画面の作りで、ページ側では変えられない

## 確かめたこと

- Chromium の main の `SelectFileDialog.java` を読んだ（2026-10-18）
- ユーザーの Pixel で、2 枚目を押してもチェックが移るだけなことを確かめた
