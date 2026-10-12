# bganalyzer

スマホで撮った実物のバックギャモン盤の写真から局面を読み取り、GNU Backgammon で解析する（勝率・ギャモン率・ピップ数）ためのプロジェクトです。最終的には PWA にする予定です。

## 現状

- `recognizer/`: ステップ1の盤面認識プロトタイプ（Python / OpenCV）。詳細は [recognizer/README.md](recognizer/README.md)。
- `samples/`: 正解データ（`*.truth.json`）。写真そのものは人物が写っているためリポジトリに含めていません。

## 予定

1. 盤面認識の試作（済）
2. gnubg による解析（サーバー側）
3. PWA（撮影・四隅指定・手修正）
4. 実写真での調整
