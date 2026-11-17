# TODO-182. collected-black-red-oblique-3 の正解で、手前の駒の色（bottom_colour）を 1 に直す

| | main | 担当 |
|---|---|---|
| 見込み | Opus 5.5 / effort medium | main（数行の変更）+ verifier（Sonnet 5.5 / low）+ reviewer（Sonnet 5.5 / low） |
| 実施 | Opus 5.5 / effort medium | main（数行の変更）+ reviewer（Sonnet 5.5 / low）+ verifier（Sonnet 5.5 / low） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | medium | 69 | 8,637 | 63,368 | 2,278,072 | 85% |
| reviewer-182（reviewer） | Sonnet 5.5 | low | 18 | 4,458 | 34,147 | 231,393 | 10% |
| verifier-182（verifier） | Sonnet 5.5 | low | 10 | 2,362 | 29,935 | 115,305 | 5% |
| 合計 |  |  | 97 | 15,457 | 127,450 | 2,624,770 | 計 2,767,774 |

- 集計は `--since '2026-11-17 14:10:30'`（項目を立てたあと TODO-183 を挟んだため）。項目を立てたときの wording-182 は含まない

## きっかけ

この写真の正解は `bottom_colour` が 0（暗い駒）のままで、写真の手前の明るい駒と合っていなかった。d708806 は盤面だけを直していた。調べたことは `archives/agents/TODO-182/main-findings.md`。

## やったこと

- `samples/collected-black-red-oblique-3.truth.json` の `bottom_colour` を 1 にし、`note` に修正を書き足した
- `recognizer/accuracy_baseline.json` のこの組の `home` を false → true にした（全件を流す `--update` を避け、該当の行だけ手で直した）
- 同じ変更で、TODO.md の TODO-025・TODO-030 に見込みの行を足した（hook の指摘。ユーザーの依頼）

## 確かめたこと

- `evaluate.py` をこの組だけで流し、points 20/24・bar ok・home guess ok・dice ok・cube ok（基準と一致。home は false から上がった）
- verifier: `bottom_colour` を 0 に戻した写しでは home guess が wrong（-16.8）になる。1 では ok（+11.4）
- reviewer: 要修正は 0 件。指摘の対応は次のとおり
  - 差分が依頼の 2 ファイルでなく 3 ファイル（TODO.md のチェック）→ 確かめた（決まりどおり）
  - `note` に修正を書いていない → 直した
  - ほかの基準の行が今の読み取りと合うか → 確かめた（CI の accuracy に任せる、と依頼に書いた範囲）

## 分担の振り返り

- reviewer は `note` の書き漏れを見つけた。verifier は、色を戻すと home の推定が外れることを示し、今回の値が読み取りに効いていることを確かめた
- 見込みと食い違いは無い
- 次に同じ規模（正解ファイルの値を 1 つ直す）なら、同じ組み方でよい。reviewer の指摘は好みの範囲 1 件だけだったので、effort は low のままで足りる。main が自分で evaluate を流しているので、verifier には「壊すと外れるか」だけを頼めば、さらに減らせる
