# TODO-182 reviewer 報告

結論: 要修正 0 件、検討 1 件、好みの範囲 1 件。

## 要修正
なし

## 検討
1. `TODO.md:56` / 差分が「2 ファイル」の依頼と 3 ファイル
   - `git diff` は 3 ファイル（truth.json・accuracy_baseline.json・TODO.md）。TODO.md は項目のチェックボックスを `[ ]`→`[x]` にしただけ。
   - 根拠: ~/.claude/CLAUDE.md「実装できた時点でチェックボックスをチェックする」。決まりどおりで問題なし。依頼の「2 ファイル」が不正確なだけ。
   - 注意: この項目の文言は `check_accuracy.py` で確かめるとあるが、依頼では `evaluate.py` をこの組だけ流す（全体は CI の accuracy）。項目の「無駄を省く工夫」にそう書いてあるので矛盾はしない。

## 好みの範囲
1. `samples/collected-black-red-oblique-3.truth.json` の `note`
   - d708806 は盤面を直したとき `note` に「Points mirrored on 2026-11-17 …」を足した。今回の `bottom_colour` の修正は `note` に書かれていない。
   - 根拠: 直前の同種の修正との比較のみ。必須ではない（CLAUDE.md に決まりはない）。

## 一致（1 行）
- 差分の中身: truth.json は `"bottom_colour": 0` → `1` の 1 箇所だけ（`git diff` で points・四隅・home=right・side=right・dice・cube・read・fixed_points は同一）。baseline は `collected-black-red-oblique-3` の `home` が false → true の 1 行だけ。ほかのサンプルの行は変化なし。
- JSON として読める（両ファイル）。baseline の行の書式・末尾の改行は元のまま。
- main-findings.md の根拠と矛盾なし: findings は「bottom_colour=0 で recognize すると暗い駒が 1・12・17・19 にあり、直した正解 points（手前 6・8・13・24）はその白黒を入れ替えたものに当たる → 手前は明るい駒（1）」。1 にする方向と合う。ただし写真そのものは見ていない（findings の主張を前提にした。「未確認」）。
- `evaluate.py:75` は `t.get("bottom_colour", 1)` で読む色を選ぶので、truth の値がそのまま `home guess` に効く。home が false → true になる理由の経路は読めた（実測は verifier）。
- ほかの参照: `analyzer/test_api.py` の `test_bottom_colour_is_guessed_from_the_pips` は samples 全部の points から白黒を両方試すだけで、`bottom_colour` の値は使わない。`test_pwa.py:781` は別のサンプルの値。この組の `bottom_colour` に依存するテスト・文書は `rg` で見つからなかった（`recognizer/README.md` の精度の表にもこの組の行なし）。
- バージョン: samples と基準だけの変更なので上げなくてよい（CLAUDE.md「バージョン」）。

## 基準の手書き修正（CLAUDE.md「精度の確認」との整合）
- 「良くなったときは `--update` で基準を書き直して同じ変更に入れる」とあり、手で 1 行直したのは手段が違うだけで、結果は同じファイルになるはず。ただし `--update` は全サンプルを再計測して全行を書き直すので、手書きだと「ほかの行が現在の読み取り結果と合っている」ことは確かめていない（未確認）。CLAUDE.md の別の決まり（全件は手元で流さない・CI の accuracy に任せる）に沿った選択で、CI の accuracy が、この組の行が悪くなっていないことと、ほかの行が崩れていないことを確かめる。したがって規約違反ではない。
- `--update` を使えば手書きでは起きない書き間違いを避けられるが、今回は 1 語の差で、diff で確認できた。
