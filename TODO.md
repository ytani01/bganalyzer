# TODO

**残っている項目: TODO-012、TODO-023。** これまでに 21 件を決着させた。
新しく足すときは「完了済み」の上に節を作る。**次の番号は `TODO-024`。**
各項目の最初に **担当**（ai1 か、共同開発者のアカウント名、未定）を書き、着手する前に自分の担当にしてコミットする
（[docs/HANDOVER.md](docs/HANDOVER.md)）。

---

## TODO-012. ネット上のサンプルで見つかった認識の弱点を直す

- **担当:** ai1
- **見込み:** main Opus 5.5 / effort medium（実装）+ reviewer（Opus 5.5 / high）+ verifier（Sonnet 5.5 に上書き / medium。evaluate.py の実測）
- TODO-011 で集めたサンプルで見つかった弱点（詳しくは [recognizer/README.md](recognizer/README.md) の「ネット上のサンプル」）:
  - [x] 三角形への合わせ直しが、盤の外の駒入れの溝や細い蝶番のバーに引っ張られてずれる（commons-travel-case 15→21/24、commons-tavli-grey 11→23/24。recognizer 0.3.1）
  - [x] 蝶番や留め具をバーの駒と数える（Commons 11 枚のバーが全部正しくなった。0.3.1）
  - [x] 盤面図で、白い三角形の上の白い駒を見落とす（USBGF 7 枚 147→166/168。0.3.1）
  - [ ] バーの帯がない盤（commons-dark-homeleft 12/24）とダイスカップが乗ったやや斜めの写真（commons-leather-cups 14/24）
  - [ ] 四隅の推定（corners.py）が Commons の写真 11 枚中 4 枚で見つからず、5 枚で 4.5〜12.9% ずれる
- dark-homeleft を調べて分かったこと（2026-10-13、Raspberry Pi で）: 暗い盤の上の焦げ茶の駒が円として見つからない。
  三角形が白・赤・黒の 3 色ある盤で、`board_colours` が三角形の色を 2 つにしか分けないので、空いた白や赤の三角形の底を駒と読む。
  直すには駒の検出と三角形の色の扱いの両方に手が入るので、全サンプルを x86_64 の環境で測りながら進める（Pi は精度の値が少し違う）。

---

## TODO-023. Raspberry Pi で確かめることを、Pi の上の Claude Code が気づくようにする

- **担当:** ai1
- マージ後に Pi でしか確かめられないこと（3手読みの時間など）を docs/PI_CHECKS.md に並べ、
  Pi の上の Claude Code が git pull のあとにそれを読んで確かめるよう、CLAUDE.md に書く。

---

## 完了済み

決着した項目は `archives/todo/` にある（1 項目 1 ファイル）。
一覧は [archives/index.md](archives/index.md)（新しい順）。やらないと決めたものは
ファイル名に（対応しない）が付いていて、理由も書いてある。蒸し返す前に読むこと。
