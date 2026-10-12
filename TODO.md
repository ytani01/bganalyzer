# TODO

新しく足すときは「完了済み」の上に節を作る。**次の番号は `TODO-007`。**
各項目の最初に **担当**（ai1 か、共同開発者のアカウント名、未定）を書き、着手する前に自分の担当にしてコミットする
（[docs/HANDOVER.md](docs/HANDOVER.md)）。

---

## TODO-006. ネット上のサンプル写真で認識精度を確かめる

- **担当:** ai1
- 実物の盤の写真を Wikimedia Commons から集める（CC0 / CC BY / CC BY-SA のみ、出典とライセンスを記録、顔や個人情報が写るものは避ける）。
  正解の `*.truth.json` を作って `samples/` に加える。
- bkgm.com・usbgf.org・timothychow.net の XGID 付き盤面図は、手元で精度を測るだけにして画像はリポジトリに入れない。

---

## 完了済み

決着した項目は `archives/todo/` にある（1 項目 1 ファイル）。
一覧は [archives/index.md](archives/index.md)（新しい順）。やらないと決めたものは
ファイル名に（対応しない）が付いていて、理由も書いてある。蒸し返す前に読むこと。
