# TODO

**残っている項目: TODO-025、TODO-027、TODO-028、TODO-029。** これまでに 25 件を決着させた。
新しく足すときは「完了済み」の上に節を作る。**次の番号は `TODO-030`。**
各項目の最初に **担当**（ai1 か、共同開発者のアカウント名、未定）を書き、着手する前に自分の担当にしてコミットする
（[docs/HANDOVER.md](docs/HANDOVER.md)）。

---

## TODO-025. キューブ判断（ダブル／テイク／パス）

- **担当:** ai1
- ユーザーの依頼（2026-10-13）: ダブルされた局面ならキューブを読み取ってテイク／パスを判定する。
  キューブもダイスも無ければ、手番側がダブルすべきかを評価する。
- 決めたこと: マネーゲーム（gnubg の既定どおりジャコビー・ルールあり、ビーバーなし）で評価する。
  ダイスがあれば従来どおりチェッカーの手を評価する。キューブが片方の側にあってダイスが無ければ
  「その側がダブルされた」とみなす。読み取れないときは画面で手で直す。
- [x] 解析（gnubg のキューブ判断）と PWA の表示・手動の設定（analyzer 0.17.0）
- [x] 写真からキューブの場所を読み取る（recognizer 0.6.0。6 枚中 3 枚、誤検出なし。0.6.1 で 4 枚）
- [ ] キューブの数字を読む（今は片側なら 2 とし、手で直す）

---

## TODO-027. 暗い盤の上の焦げ茶の駒を見つける（commons-dark-homeleft）

- **担当:** 未定
- **見込み:** main Opus 5.5 / effort high（設計と実装）+ reviewer（Opus 5.5 / high）+ verifier（Sonnet 5.5 / medium。evaluate.py の実測）
- [ ] commons-dark-homeleft（Raspberry Pi で 12/24）を、ほかのサンプルを下げずに上げる

TODO-012 から分けた。分かっていること（2026-10-14、Raspberry Pi で測定）:

- 列の位置はほぼ合っている（バーの帯の代わりに盤の継ぎ目がある）。外しているのは、焦げ茶の駒の見落とし（1・12・17・19 ポイント）と、
  空いた三角形の赤・クリームの部分を駒と読むこと（3・5・11・14〜16・21）。13 ポイントの白い駒は、焦げ茶の駒が少ないため色の分け方がずれて黒と読む。
- 三角形は白い縁取りの黒で、底の側だけ赤とクリームで塗ってある（3 色）。`board_colours` は三角形の色を 2 つに分けるので、赤が入らない。
- 焦げ茶の駒は Lab の縁の強さ（しきい値 40）が 0.03〜0.42 で、Hough では 15 個中 3 個しか出ない。
  CLAHE（局所コントラスト強調）をかけたグレーでは 11〜14 個出て、縁の強さも 0.30〜0.86 になるが、空いた三角形の底（0.38〜0.55）と重なる。
- CLAHE を Hough の入力に足し、縁の強さを Lab と CLAHE の大きい方にすると、ほかの盤で模様も駒と読み、全サンプルで 492 → 429 ポイントに下がった。
- 同じ色の列の中央値を「空いたときの見た目」にして比べる方法は、初期配置では同じ色の列に駒が多く、中央値が駒に引っ張られて分けられなかった。
- 直すには、候補（CLAHE など）と、三角形の色を 3 つまで扱う空いた所の色の見積もりを、両方変える必要がある。

---

## TODO-028. 四隅の推定（corners.py）を作り直す

- **担当:** 未定
- **見込み:** main Opus 5.5 / effort high（設計と実装）+ reviewer（Opus 5.5 / high）+ verifier（Sonnet 5.5 / medium。四隅のずれの実測）
- [ ] `corners.find_corners` が見つからない・大きくずれるサンプルを減らす

TODO-012 から分けた。Raspberry Pi で全 23 枚を元の大きさのまま測った結果（2026-10-14、目視の四隅とのずれの最大、写真の長辺に対する割合）:

- 3.6% 以内: diagram-holding 3.0%、nardy-midgame 2.5%、tavli-red-white 3.6%、photo2 2.7%、photo3 2.7%、screen2 2.8%
- 大きくずれる: set-cube-dice 14.3%、tavli-burl 13.6%、tavli-red-brown 11.9%
- 見つからない（14 枚）: case-dice、case-midgame、dark-homeleft、diagram-closed-bar、diagram-prime、leather-cups、rollup-oblique、
  tavli-black、tavli-blue、tavli-grey、tavli-red-diamond、travel-case、photo4、screen1
- recognizer/README.md の記録（x86_64、Commons 11 枚中 4 枚が見つからない）より見つからない写真が多い。
  Pi と x86_64 の違い（k-means など）かどうかは確かめていない。着手したらまず x86_64 でも測る。
- 色を 8 つに分けて細長い三角形の領域を探す今の作り方は、三角形が駒に隠れる・縁取りだけの三角形・盤面図の木目で崩れやすい。
  作り直しの方針（例: board.py の三角形の先端の探し方を使う、縁の直線から探す）は着手するときに決める。

---

## TODO-029. Raspberry Pi で photo3 のキューブが見つからない

- **担当:** ai1
- **見込み:** main Opus 5.5 / effort medium（原因の切り分け）+ verifier（Sonnet 5.5 / medium。evaluate.py の実測）。直すことになったら reviewer（Opus 5.5 / high）も入れる
- [x] Pi で photo3 のキューブ（中央）が読めない原因を確かめ、直すか、Pi と x86_64 の違いとして残すかを決める
  （2026-10-13: x86_64 でも見つかる回数が 7 回で、必要な 6 回のぎりぎりだった。JPEG で保存し直すだけで 4〜5 回に落ちて見つからない。
  必要な回数を 4 回に下げ、2 番目の候補の 2 倍以上あることも条件にした。recognizer 0.6.1。キューブの写った 6 枚中 4 枚（set-cube-dice も読めるようになった）、誤検出なし）
- [ ] Pi で PI-008 を確かめ直し、photo3 が `cube ok` になる
- [ ] Pi では photo3 のキューブの数字「64」が 5〜7 個の印に割れ、`1 <= marks <= 4` で落ちる（2026-10-14、recognizer 0.6.1。塊は 8 段階で見つかっている）。印の上限を 8 にする（Pi の全サンプルで photo3 だけが変わり、誤検出なし）

PI-008（2026-10-14、f3dac73、recognizer 0.6.0）で分かった。コンテナの中で evaluate.py を動かすと、photo3 が
`cube not found (read None, truth centre)` になる。screen2（`cube ok (read black)`）と photo4（キューブなし）は期待どおり。
PI-008 の期待では photo3 も `cube ok (read centre)` で、x86_64 では読めていたはず。
Pi は盤の認識でも値が少し違う（recognizer/README.md の「精度」）ので、まず x86_64 で photo3 を測り直し、Pi だけで起きるかを確かめる。

---

## 完了済み

決着した項目は `archives/todo/` にある（1 項目 1 ファイル）。
一覧は [archives/index.md](archives/index.md)（新しい順）。やらないと決めたものは
ファイル名に（対応しない）が付いていて、理由も書いてある。蒸し返す前に読むこと。
