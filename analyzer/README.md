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

1. 「写真を撮る」でカメラを開くか、「写真を選ぶ」で端末の写真を選ぶ（アプリ画面のスクリーンショットも可）。「写真なしで入力する」で初期配置から手入力もできる。
2. 盤の遊戯面の四隅に初期値の点が出る（`/find-corners` で推定。見つからないときは画像の内側の長方形）。
   ずれていればドラッグで合わせる（指の下はルーペで拡大表示）。「四隅をやり直す」で 左上→右上→右下→左下 の順にタップし直すこともできる。
   手前の人のホーム側（自動/左/右。自動なら駒の並びから推測）と駒の色（暗い方/明るい方）を選んでヘッダーの「盤面を読み取る」。
3. 読み取った盤面が出るので、違うポイントやバーをタップして駒の数を直す。駒の色・左右の入れ替えボタンもある。
   ホーム側を自動にしたときは、推測した側をボタンの下に出す（逆なら「左右を入れ替える」）。
   盤の上に転がっている 2 つのダイスが写真から読めたときは、ダイスの目に初期値として入る（「写真からダイスの目を読み取りました」と出るので、違えば直す）。
   読めないとき・自信がないとき（1 つしかない、3 つ以上ある、バーやカップの中など）は空のまま。
   次に振る人とダイスの目（任意）、読みの深さ（2手 / 3手。選んだほうを端末に覚える）を選んでヘッダーの「解析する」。ダイスの目が入っているときは、盤面図にもダイスの絵が出る
   （次に振る人の右手側のフィールド、つまり手前なら右・奥なら左に、その人の駒の色で）。
   **キューブ**は場所（中央 / 手前 / 奥）と数を選ぶ（`static/cube.js`。盤面図のバーにも出る）。写真から場所が読めたときは初期値に入る
   （「写真からキューブを読み取りました」と出る。数は読まないので片側なら 2。違えば直す）。ダイスがなければ、中央なら次に振る人がダブルすべきかを、
   片側にあれば「その側がダブルされたところ」としてテイクかパスかを判定する（次に振る人はダブルした側に自動で変わる）。
   「ダブルされたところ」を外すと、その側がキューブを持っている扱いになる（持ち主が次に振るならリダブルすべきかを判定）。
   「手番を入れ替える」で次に振る人を反対にできる（解析の結果が出ていれば、そのまま新しい手番で解析し直す）。
4. 解析すると**結果の画面**に移る。上に盤面図（ここでは直せない）、下に勝率・ギャモン率・エクイティ・ピップ数と、ダイスを入れたときは最善手5つ。
   直すときはヘッダーの戻る（スマホの戻るでも）で盤面の画面に戻る。盤面も設定も変えずにもう一度「解析する」を押すと、解析し直さずに同じ結果を出す。
   最善手は盤面図に矢印で出る（最初は 1 位の手。一覧の行をタップするとその手の矢印に変わる。ヒットした先は赤い丸。手の表記の読み方は `static/moves.js`）。盤面を直すと矢印は消える。
   写真から読み取ったときは、元の写真も出して読み間違いを見比べられる（下記）。
   ヘッダーの「🔊」ボタン（解析したあとに出る。読んでいる間は「■」で止める）で、ダイスを入れたときは最善手を最初に、続けて勝率・ギャモン率・ピップ数を日本語で読み上げる（ダイスがないときは最後に次に振る人）。
   ブラウザ標準の音声合成（Web Speech API）を使うので無料で、サーバーには何も送らない。Android の Chrome では Google の音声になる。

**元の写真の表示（`static/photo.js`）:** 四隅で台形補正した写真を、盤面図と同じ向き・同じポイントの並びで出す。
「並べる」（広い画面では左右、スマホでは上下）と「隠す」を選べる。
写真側のポイントをタップしても同じポイントが選ばれる。補正には `/analyze-photo` が返す `geometry`
（認識が見つけた盤の四隅と列の位置）を使い、写真の列を盤面図の列にそろえる。補正は端末の中で行い、写真を追加で送ったり保存したりはしない。

- 読み込んだ写真は、最近の 3 枚まで「最近の写真」に残る（`static/history.js`）。写真を選んだ時点で入り、
  選ぶと盤面を読み取る前の四隅の画面から、指定した四隅・ホーム側・駒の色のまま始まる。読み取って直した盤面も残っていて、
  「前に読み取った盤面を開く」で開ける。残すのは**使っている端末の中（IndexedDB）だけ**で、サーバーには残らない。
  写真は長辺 2048px に縮めて（小さいスクリーンショットはそのまま）保存し、古いものから自動で消える。✕ で 1 枚ずつ消せる。
- 長辺 2560px を超える写真は、ブラウザで長辺 2048px に縮めてから送る（この大きさでのサンプルの精度は [recognizer/README.md](../recognizer/README.md) の「精度」の「アプリ経由」の列）。
- 別のホストに PWA を置くときは `?api=https://APIのURL` を付けて開く。
- ホーム画面への追加と Service Worker は HTTPS（または localhost）のときだけ有効。
- **Android** でホーム画面に追加すると、写真アプリなどの「共有」の一覧に BG Analyzer が出る（manifest の `share_target`）。
  共有した写真は Service Worker が端末の中で受け取り（`sw.js`）、選んだときと同じく四隅の指定に進む。サーバーに送るのは「盤面を読み取る」のときだけ。
  Service Worker がまだ動いていないとき（追加した直後など）は、サーバーの `POST /share-target` が写真を読まずにアプリへ戻し、選び直すよう表示する。
  iPhone（Safari）には PWA を共有先にする仕組みがないので、アプリ内で選ぶ。

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
| `cube_value` | キューブの数 1, 2, 4, …, 64（既定 1 = 中央） |
| `cube_owner` | キューブの持ち主 `"white"` / `"black"`、中央なら `null`（既定）。数が 2 以上なら持ち主が要る |
| `doubled` | `true` なら、`on_roll` の側が今 `cube_value` にダブルし、`cube_owner`（相手側）がテイクかパスかを決めるところ（ダイスとは一緒に使えない） |

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
- **キューブ判断（`cube`）:** ダイスがないとき、`on_roll` の側がダブル（リダブル）できるなら、gnubg のキューブ判断を返す
  （マネーゲーム、gnubg の既定どおりジャコビー・ルールあり・ビーバーなし。深さは `plies`）。ダイスがあるとき、相手がキューブを持っているときは `null`。

  ```json
  "cube": {"question": "double", "doubler": "white", "taker": "black", "value": 1,
           "equity": {"no_double": 0.81, "double_take": 0.899, "double_pass": 1.0},
           "double": true, "too_good": false, "take": true, "proper": "Double, take"}
  ```

  `question` は `"double"`（ダブルすべきか）か `"take"`（`doubled: true` のとき。テイクかパスか）。`value` はダブルする前のキューブの数、
  `equity` はダブルする側から見たキューブありのエクイティ（ダブル前のキューブ 1 つ分を単位とする）。`too_good` はダブルせずギャモンを狙う方がよい局面。
  `proper` は gnubg の言葉そのまま。gnubg の Python モジュールにはキューブ判断を返す関数がないので、解析用の子プロセスで gnubg の
  `hint` コマンドを実行し、表示された文字を読んでいる（`analysis.py` の `_cube_hint`）。

### `POST /find-corners`（multipart）

フィールド `image`。盤の遊戯面の四隅の推定（`recognizer/corners.py`）を返す:
`{"corners": [[x, y] × 4（左上・右上・右下・左下、送った画像の画素）] または null, "width": 幅, "height": 高さ}`。
PWA は写真を読み込んだ直後に、`/analyze-photo` と同じ大きさに縮めた写真を送り、結果を四隅の初期値にする。

### `POST /analyze-photo`（multipart）

写真から認識（`recognizer/board.py`）して、そのまま解析します。
フィールド: `image`、`corners`（`x1,y1,…,x4,y4`）、`home`（`left`・`right`・`auto`。既定 `right`）、
`bottom_colour`（意味は recognizer/README.md と同じ）、`on_roll`、`plies`、`dice`（例 `3,1`。省くと写真から読めたダイスを使う）、`cube_value`・`cube_owner`・`doubled`（/analyze と同じ）。

応答は `{"recognized": 認識結果, "home": "left" か "right", "home_guess": {...} か null, "errors": [...], "warnings": [...], "geometry": {...}, "dice_read": [大, 小] か null, "analysis": 上の /analyze と同じ形}`。
`dice_read` は写真のフィールドに 2 つのダイスがあって、目を自信を持って読めたときだけ入る（recognizer/README.md の「ダイス」）。
`dice` を送らなかったときは、これで最善手も出す。
`cube_read` は写真で見つけたキューブの場所 `{"at": "centre" | "white" | "black"}`（数字は読まない）か `null`（recognizer/README.md の「キューブ」）。
`cube_value` を送らなかったときは、これで解析する: 片側にあれば数を 2 とし、ダイスが無ければ反対側がダブルしたところとして
テイクかパスかを判定する（`analysis.on_roll` がダブルした側になる）。ダイスがあればその側が持っているキューブとみなす。
`home` は読み取りに使った側。`home=auto` のときは駒の並びから推測した側で、`home_guess` に
`{"margin": 尤もらしさの差（正なら右、負なら左。絶対値が 1 未満なら決めずに右）}` が入る。
`geometry` は認識が見つけた遊戯面の位置: `corners`（送った画像の画素で 左上・右上・右下・左下）、
`columns`（12 列の中心、左から。遊戯面の幅に対する割合）、`bar`（バーの左右の端、同じく割合）。
`warnings` は写真についての注意（日本語の文）。今は、盤を真上から 40° 以上傾けて撮ったときに「斜めから撮った」と出る。
認識で駒数が合わないときは `analysis` が `null` になり、`errors` に理由が入ります（アプリで手修正してから
`/analyze` を呼ぶ想定）。

### `GET /health`

`{"ok": true}` を返す（Docker の healthcheck 用）。

### `GET /version`

```json
{"analyzer": "0.1.0", "recognizer": "0.1.0", "commit": "7bd7f55"}
```

analyzer（この API と PWA）と recognizer のバージョン、動いているコードの git のコミット ID（取れなければ `null`）。
PWA は画面のいちばん下にこれを出す。上げ方は [CLAUDE.md](../CLAUDE.md) の「バージョン」。

## テスト

```
uv run pytest analyzer
```
