# TODO-162. キューブのダブルのボタンの文言を「〜から〜にダブル」にする

|      | main | 担当 |
|------|------|------|
| 見込み | Sonnet 5.5 / effort medium | implementer（Sonnet 5.5）+ verifier（Sonnet 5.5）。文言だけなのでレビューは付けない |
| 実施 | Opus 5.5 / effort 記載なし | implementer（teammate、Sonnet 5.5 / 記載なし）+ verifier（teammate、Sonnet 5.5 / 記載なし） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main（teammate の分を含む） | Opus 5.5 + Sonnet 5.5 | 記載なし | TODO-161 の記録に合算 | | | | |

- TODO-161 と同じ作業（2 つの PR をまとめて進めた）なので、トークンは [TODO-161 の記録](TODO-161.%20ヘッダーの手順の一覧をやめる.md)にまとめて書いた。重ねて数えない

分担は [archives/agents/TODO-161/](../agents/TODO-161/)（TODO-161 と TODO-162 をまとめて確認した verifier の報告）。

## きっかけ

キューブの置き方のボタン「白に対してダブル」「黒に対してダブル」が分かりにくかった。2026-10-20 にユーザーが「黒から白にダブル」「白から黒にダブル」に変えると決めた（`data-value="white"` が「黒から白にダブル」、`"black"` が「白から黒にダブル」）。

## やったこと

PR #481（#480 のコミットを含む）、analyzer 0.89.3。

- `analyzer/static/index.html` のボタンを `<span class="nm-black">黒</span>から<span class="nm-white">白</span>にダブル` と、その逆の形にした（span は `app.js` が名前に差し替える）
- `analyzer/README.md` と `docs/raspi.md` の「…に対してダブル」を「…にダブル」にし、README のキューブの説明に、2 つのボタンのどちらが誰がダブルされたところかを書いた

## 確かめたこと

- verifier が、`bottomColour` の既定（1）と 0 の両方でボタンの文言を測った
- ローカル（開発機、マージ後）: サービスの版 0.89.3。`bottomColour` が 1 のとき white =「黒から白にダブル」、black =「白から黒にダブル」。0 のときは名前が入れ替わって white =「白から黒にダブル」、black =「黒から白にダブル」だった。置き方の 2 つは「白側に置く」「黒側に置く」のまま
- `rg -n "に対してダブル" --glob '!archives/**'` に残るのは、旧文言を背景として引いている `TODO.md` だけ

## 分担の振り返り

TODO-161 の記録の「分担の振り返り」と同じ（2 項目を 1 つの流れで進めた）。
