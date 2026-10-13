# TODO-006. ネット上のサンプル写真で認識精度を確かめる

**担当:** ai1

- 実物の盤の写真を Wikimedia Commons から集める（CC0 / CC BY / CC BY-SA のみ、出典とライセンスを記録、顔や個人情報が写るものは避ける）。
  正解の `*.truth.json` を作って `samples/` に加える。
- bkgm.com・usbgf.org・timothychow.net の XGID 付き盤面図は、手元で精度を測るだけにして画像はリポジトリに入れない。

**2026-10-13 の結果（ai1 のスレッド）:** Commons の写真 11 枚を `samples/commons-*` に入れた（出典は `samples/CREDITS.md`）。
ai1 の指示で、代表的なサンプルは再利用できるようにリポジトリに保存する。精度は 264 ポイント中 210。
真上から撮った Tavli の盤 6 枚は 23〜24 だが、駒入れの溝がある盤・細い蝶番のバー・ダイスカップのある写真で大きく外れる。
USBGF の Bray's Learning Curve の盤面図 7 枚は URL と正解だけを `samples/external/` に置き（画像は `evaluate.py` が取ってくる）、168 ポイント中 147。
盤面図の XGID は会員限定だったので、正解は目で読み、図のピップ数と一致することを確かめた。
bkgm.com と timothychow.net には盤面図の画像が見つからなかった（www.timothychow.net はつながらない）。
Commons 由来の写真はアクセス制限が厳しく、1 枚に数分かかった。見つかった弱点は TODO-007 にした。

## 決着

2026-10-13、サンプルを入れて精度を測ったので完了にした。
