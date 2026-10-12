# 局面解析 API（ステップ2）

盤面（gnubg Position ID、または認識結果の `points`）を GNU Backgammon で解析し、
勝率・ギャモン率・バックギャモン率・エクイティ・ピップ数と、どちらが有利かを返す HTTP API です。
PWA（下記）から呼び出します。

GNU Backgammon 本体は PyPI の [`gnubg`](https://pypi.org/project/gnubg/) パッケージ（gnubg のニューラルネットと
ベアオフDBを同梱した Python バインディング）を使います。apt で gnubg を入れる必要はありません。

## 起動

```
uv sync
uv run uvicorn app:app --app-dir analyzer --host 0.0.0.0 --port 8000
```

`--reload` や複数ワーカーは使わないでください。gnubg の拡張モジュールはメインスレッド以外で
1手読み以上の評価をするとクラッシュするため、解析は専用の子プロセス（そのメインスレッド）で行っています。

## PWA（ステップ3）

起動したサーバーの `/` をスマホのブラウザで開くと使えます（`analyzer/static/`、ビルド不要の HTML / JS）。

1. 写真を撮る / 選ぶ（アプリ画面のスクリーンショットも可）。「写真なしで入力する」で初期配置から手入力もできる。
2. 盤の遊戯面の四隅を 左上→右上→右下→左下 の順にタップ（ドラッグで調整、指の下はルーペで拡大表示）。
   手前の人のホーム側（左/右）と駒の色（暗い方/明るい方）を選んで「盤面を読み取る」。
3. 読み取った盤面が出るので、違うポイントやバーをタップして駒の数を直す。駒の色・左右の入れ替えボタンもある。
   次に振る人とダイスの目（任意）を選んで「解析する」。勝率・ギャモン率・エクイティ・ピップ数と、ダイスを入れたときは最善手5つを表示。

- 長辺 2560px を超える写真は、ブラウザで長辺 2048px に縮めてから送る（この大きさでのサンプルの精度は [recognizer/README.md](../recognizer/README.md) の「精度」の「アプリ経由」の列）。
- 別のホストに PWA を置くときは `?api=https://APIのURL` を付けて開く。
- ホーム画面への追加と Service Worker は HTTPS（または localhost）のときだけ有効。

## Docker

```
docker build -t bganalyzer .
docker run --rm -p 8000:8000 bganalyzer     # http://localhost:8000/
```

x86_64 と arm64（Raspberry Pi）の両方でビルドできる。arm64 には gnubg の wheel がないので、ソースからビルドする。
自宅の Raspberry Pi で公開する手順は [docs/raspi.md](../docs/raspi.md)（`compose.yaml` と Tailscale Funnel）。PWA は API を相対パスで呼ぶので、`/bg/` のようなパスの下に置いても動く。

## API

色の呼び方は認識側と同じです: **white = 写真の手前のプレイヤー、black = 奥のプレイヤー**。

### `POST /analyze`（JSON）

| フィールド | 説明 |
|---|---|
| `position_id` | gnubg Position ID（`board` とどちらか一方） |
| `board` | `{"points": [24個], "bar_white", "bar_black", "off_white", "off_black"}`。`points[i]` は手前側から見たポイント i+1、正 = white、負 = black。off は省略すると 15 − 残りで補完 |
| `on_roll` | 次にサイコロを振る側 `"white"`（既定）/`"black"` |
| `plies` | 読みの深さ 0〜3（既定 2。2 で 1局面 約30ms、3 で 約0.7秒） |
| `dice` | 例 `[3, 1]`。指定すると最善手の候補（上位5つ）も返す |

```
curl -s localhost:8000/analyze -H 'content-type: application/json' \
  -d '{"position_id":"4HPwATDgc/ABMA","dice":[3,1]}'
```

応答（抜粋）:

```json
{
  "position_id": "4HPwATDgc/ABMA", "on_roll": "white", "plies": 2, "game_over": false,
  "pips": {"white": 167, "black": 167, "leader": null, "difference": 0},
  "probabilities": {"white": {"win": 52.5, "gammon": 14.9, "backgammon": 0.7},
                    "black": {"win": 47.5, "gammon": 12.5, "backgammon": 0.5}},
  "equity": {"white": 0.076, "black": -0.076},
  "favourite": "white",
  "moves": [{"move": "8/5 6/5", "equity": 0.16}],
  "summary": "手前が有利: 勝率 52.5%（ギャモン 14.9%）、ピップ 手前 167 / 奥 167"
}
```

- 確率は %、`gammon` / `backgammon` はその側が勝つ場合の内訳（勝率に含まれる）。
- `equity` はキューブなし（cubeless）のマネーゲームのエクイティ。+1 が確実なシングル勝ち。
- `favourite` はエクイティが高い側。片方が15個上げ終わっていれば `game_over: true`。
- 駒が15個ずつでない、Position ID が不正などは 422 とエラーメッセージ。

### `POST /analyze-photo`（multipart）

写真から認識（`recognizer/board.py`）して、そのまま解析します。
フィールド: `image`、`corners`（`x1,y1,…,x4,y4`）、`home`、`bottom_colour`（意味は recognizer/README.md と同じ）、
`on_roll`、`plies`、`dice`（例 `3,1`）。

応答は `{"recognized": 認識結果, "errors": [...], "analysis": 上の /analyze と同じ形}`。
認識で駒数が合わないときは `analysis` が `null` になり、`errors` に理由が入ります（アプリで手修正してから
`/analyze` を呼ぶ想定）。

### `GET /health`

## テスト

```
uv run pytest analyzer
```
