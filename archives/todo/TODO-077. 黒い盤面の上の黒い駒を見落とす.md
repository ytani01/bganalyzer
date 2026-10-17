# TODO-077. 黒い盤面の上の黒い駒を見落とす

|      | main | 担当 |
|------|------|------|
| 見込み | Opus 5.5 / effort high | main（測定・実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |
| 実施 | Opus 5.5 / effort high | main（測定・実装）+ reviewer（Opus 5.5 / high）+ verifier（Haiku 5.5 / medium） |

| 担当 | モデル | effort | input | output | cache_creation | cache_read | 割合 |
|------|--------|--------|-------|--------|----------------|------------|------|
| main | Opus 5.5 | high | 88 | 22,800 | 106,913 | 4,116,071 | 89% |
| reviewer | Opus 5.5 | high | 20 | 3,719 | 52,159 | 344,174 | 8% |
| verifier | Haiku 5.5 | medium | 10 | 2,857 | 31,627 | 98,923 | 3% |
| 合計 |  |  | 118 | 29,376 | 190,699 | 4,559,168 | 計 4,779,361 |

- 立ててから着手まで別の項目を挟んだので、`--since '2026-10-17 08:23:50'`（着手した時刻）から数えた
- reviewer と verifier は定義（`~/.claude/agents/`）のモデル・effort のまま（reviewer は opus / high、verifier は haiku / medium）

## きっかけ

`samples/photo5.jpg`（TODO-076）で black の駒を見落とす。立てたとき（recognizer 0.22.1）は 22/24 で、
1 ポイントと 6 ポイントの black 2 個ずつ（黒い盤面の、枠に接した下の段）が読めていなかった。

## やったこと

- 見落とす理由を測った。円の候補は、`radial.PEAK_REL` を 25% から 5% まで下げてやっと出るが、輪郭は全周の 39〜53%、
  色は空いた盤面との差が 0.5〜9 で、同じくらいの値の偽の候補（165,952 など）と見分けられない。閾値を下げる案はやめた
- 円の代わりに、三角形の縁が隠れていることで山を拾う `add_hidden_stacks` が働いていなかった。`column_texture` は行ごとの
  横 / 縦のエッジの比を行の中央値と比べるが、photo5 の下の段は 12 列中 7 列が駒で覆われ、中央値が 1.4（`TEX_MIN` 3.0 未満）に落ちて、その行を使っていなかった
- `recognizer/checkers.py` の `column_texture`: 中央値が `TEX_MIN` に届かないとき、上位 25% を基準にする。それが
  `TEX_MIN_COVERED`（4.0）に届かなければ、今までどおりその行は使わない。上位 25% は photo5 で 4.7、commons-leather-cups（三角形の縁が弱い盤）で 3.2。
  4.0 の条件を付けないと leather-cups の 11 ポイントでカップを駒の山と読み、-4 が出た
- `recognizer/tune.py` の試す定数に `TEX_MIN_COVERED` を足した
- recognizer 0.23.0 → 0.23.1、`recognizer/README.md` の「精度」の photo5、`recognizer/accuracy_baseline.json`（photo5 22 → 24 の 1 行だけ。964/1080）

「何を決めるか」に書いた「閾値を下げるか、別の手掛かりを足すか」は、どちらでもなく、すでにある手掛かり（三角形の縁）の基準の直しで済んだので、利用者には聞いていない。

## 確かめたこと

- photo5・commons-tavli-black・commons-dark-homeleft・commons-leather-cups と、利用者に言われた collected-l9azfe の 5 枚で前後を比べ、変わったのは photo5（22 → 24）だけ
- verifier: 5 枚の読みが期待どおり。`TEX_MIN_COVERED = 99`（分岐を外す）で photo5 が 22 に、`3.0` で leather-cups が 14 に戻る（`archives/agents/TODO-077/verifier-report.md`）
- PR #306 の GitHub Actions の `test` と `accuracy` が通った

## 残ること

- photo5 の home の推測は外れたまま（+16.5）。読みは正しいので、局面から home を推測する側の話で、この項目では扱っていない
- reviewer の指摘: 上位 25% を基準にした行では、上の 3 列前後に必ず "shown" が付く。斜めの写真で山の側面が上位に入ると、その山の円が候補から落ちうる。
  全サンプルの基準の書き直しで photo5 以外の読みは変わらなかったので、今のサンプルでは実害は出ていない。4.0 も 2 枚（3.2 と 4.7）の間に置いた値

## 分担の振り返り

- reviewer は、代わりの基準を使う行で "shown" が増える筋（photo5 で 4 列）と、`continue` で書けば判定が 1 つで済むことを見つけた。後者とコメントの直しは取り込んだ
- verifier は食い違いを見つけなかった。分岐を外す・閾値を下げると読みが崩れることを実測で示し、変更が効いていることの裏付けになった
- 見込みと食い違わなかった。次に同じ規模（定数 1 つと分岐 1 つ）なら同じ組み方でよいが、verifier の 3 手順のうち 1 は main が前後の比較で済ませていたので、2・3 だけ頼めば足りた
