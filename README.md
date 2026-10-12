# bganalyzer

スマホで撮った実物のバックギャモン盤の写真から局面を読み取り、GNU Backgammon で解析する（勝率・ギャモン率・ピップ数）ためのプロジェクトです。スマホのブラウザで使う PWA から写真を送って解析できます。

図の中で点線・「予定」と書いた部分はまだ作っていません。

## 全体のソフトウェア構成

利用者のスマホで動く PWA が写真を撮り、サーバーの解析 API に送ります。PWA の画面（HTML / JS）も同じサーバーが配信します。サーバーは盤面認識（OpenCV）と局面解析（GNU Backgammon）を行い、結果を JSON で返します。

```mermaid
flowchart LR
    subgraph phone["スマホ（ブラウザ）"]
        pwa["PWA（analyzer/static/）<br/>撮影・四隅タップ<br/>自分の色・ホーム側の指定<br/>認識結果の手修正・結果表示"]
    end

    subgraph server["解析サーバー（Python）"]
        api["analyzer/app.py<br/>HTTP API（FastAPI + uvicorn）"]
        rec["recognizer/<br/>盤面認識（OpenCV）"]
        ana["analyzer/analysis.py<br/>局面解析"]
        gnubg[("GNU Backgammon<br/>（PyPI gnubg パッケージ<br/>ニューラルネット・ベアオフDB同梱）")]
        api --> rec
        api --> ana
        ana --> gnubg
    end

    pwa -- "HTTP(S) / JSON・multipart" --> api
```

| 層 | 場所 | 技術 | 状態 |
|---|---|---|---|
| 画面（撮影・手修正・結果表示） | スマホのブラウザ | PWA（素の HTML / JS、ビルド不要） | 済（ステップ3） |
| HTTP API | サーバー | FastAPI / uvicorn | 済（ステップ2） |
| 盤面認識 | サーバー | Python / OpenCV | 済（ステップ1） |
| 局面解析 | サーバー（子プロセス） | GNU Backgammon（gnubg） | 済（ステップ2） |

## モジュール構成

```mermaid
flowchart TB
    subgraph analyzer["analyzer/（ステップ2・3）"]
        app["app.py<br/>FastAPI のエンドポイント<br/>/analyze, /analyze-photo, /health<br/>/ で static/ を配信"]
        analysis["analysis.py<br/>gnubg 呼び出し・確率/エクイティ整形<br/>日本語の要約"]
        worker["gnubg 子プロセス<br/>（そのメインスレッドで評価）"]
        test["test_api.py<br/>API のテスト"]
        static["static/<br/>PWA（index.html, app.js,<br/>manifest, Service Worker）"]
    end

    subgraph recognizer["recognizer/（ステップ1）"]
        board["board.py<br/>写真 → 盤面（認識本体）"]
        position["position.py<br/>盤面モデル・Position ID・ピップ数"]
        synth["synth.py<br/>合成画像の生成（正解付き）"]
        evaluate["evaluate.py<br/>正解と比べて精度を出す"]
    end

    samples[("samples/<br/>写真・画面と正解 *.truth.json")]

    static -- "fetch" --> app
    app --> analysis
    app -- "/analyze-photo のときだけ読み込む" --> board
    analysis --> position
    analysis -- "ProcessPoolExecutor" --> worker
    board --> position
    synth --> position
    evaluate --> board
    evaluate --> samples
    test --> app
```

| ファイル | 役割 |
|---|---|
| `recognizer/board.py` | 写真＋四隅 → 射影変換 → 三角形・縁で補正 → 駒を円として検出 → ポイントごとに数える。コマンドラインでも使える |
| `recognizer/position.py` | 盤面モデル（`points` 24個・バー・上がり）、gnubg Position ID の作成/読み込み、ピップ数。認識と解析の共通の型 |
| `recognizer/synth.py`, `evaluate.py` | 精度確認用（合成画像の生成、`samples/*.truth.json` との比較） |
| `analyzer/app.py` | HTTP API。JSON の盤面または写真を受け取り、認識・解析して返す |
| `analyzer/static/` | PWA。写真を選ぶ → 四隅をタップ（ルーペ付き・ドラッグで調整）→ `/analyze-photo` → 盤面を表示してタップで修正 → `/analyze` → 勝率・ギャモン率・ピップ・最善手を表示。長辺 2560px を超える写真は 2048px に縮めて送る |
| `analyzer/analysis.py` | gnubg で勝率・ギャモン率・エクイティ・最善手を計算。gnubg はメインスレッド以外で落ちるので専用の子プロセスで動かす |

詳しくは [recognizer/README.md](recognizer/README.md) と [analyzer/README.md](analyzer/README.md) を見てください。

## 処理の流れ（写真から解析まで）

```mermaid
sequenceDiagram
    actor U as 利用者
    participant P as PWA
    participant A as app.py
    participant R as board.py
    participant G as analysis.py + gnubg

    U->>P: 盤を真上から撮影し、四隅をタップ
    P->>A: POST /analyze-photo（画像・四隅・ホーム側・自分の色）
    A->>R: recognize()
    R-->>A: 盤面（points / bar / off）と errors
    alt 駒が15個ずつそろった
        A->>G: analyze(盤面, 手番, 読みの深さ)
        G-->>A: 勝率・ギャモン率・エクイティ・ピップ数
        A-->>P: 認識結果 + 解析結果
    else 駒数が合わない
        A-->>P: 認識結果 + errors（analysis は null）
        U->>P: 盤面を手で修正
        P->>A: POST /analyze（修正した盤面）
        A->>G: analyze()
        G-->>A: 解析結果
        A-->>P: 解析結果
    end
    P-->>U: どちらが有利か・勝率などを表示
```

## ネットワーク構成

### 今（開発中）

uv か Docker で起動し、PC やスマホ（同じ LAN）のブラウザで `http://<マシンのIP>:8000/` を開きます。
http のままでも写真の撮影・解析はできますが、ホーム画面への追加（インストール）とオフライン用の Service Worker は
HTTPS（または localhost）でしか有効になりません。

手元で動かすだけなら Docker は要りません。[uv](https://docs.astral.sh/uv/) で依存を入れて起動します
（`pyproject.toml` と `uv.lock` で版を固定）。

```bash
uv sync
uv run uvicorn app:app --app-dir analyzer --host 0.0.0.0 --port 8000
```

#### uv と Docker の役割

| | 管理するもの | 使う場面 |
|---|---|---|
| uv | Python のパッケージ（gnubg、FastAPI、OpenCV など）と Python 本体の版 | 手元での開発・テスト・起動。これだけで足りる |
| Docker | OS のライブラリ（gnubg が使う glib など）も含めた実行環境まるごと | サーバーに公開するとき、どのマシンでも同じ環境で動かすため（必須ではない） |

Docker イメージの中でも、Python のパッケージは同じ `uv.lock` から `uv sync --frozen` で入れています。

```bash
docker build -t bganalyzer .
docker run --rm -p 8000:8000 bganalyzer
```

```mermaid
flowchart LR
    dev["PC / スマホのブラウザ<br/>curl / テスト"] -- "HTTP :8000" --> uv["uvicorn<br/>（ワーカー1つ・--reload なし）"]
    subgraph host["開発マシン"]
        uv --> app["app.py"]
        app --> child["gnubg 子プロセス"]
    end
```

### 予定（公開後）

ホスティング先は未定です。gnubg が子プロセスとメインスレッドを必要とするため、サーバーレス関数ではなく常駐する Python プロセス（コンテナや VPS）で動かす想定です。
リポジトリ直下の `Dockerfile` でそのままコンテナにできます。PWA は同じサーバーから配信するのが一番簡単ですが、
別の静的ホスティングに置く場合は `?api=https://APIのURL` を付けて開けば、その API を呼びます。

```mermaid
flowchart LR
    phone["スマホ<br/>PWA"]
    static["静的ファイル配信<br/>HTML / JS / manifest / Service Worker<br/>（今は API サーバーが兼ねる）"]
    subgraph backend["API + PWA サーバー（ホスティング先は未定）"]
        tls["HTTPS 終端<br/>（リバースプロキシ等）"]
        uv["uvicorn + app.py<br/>（ワーカー1つ）"]
        child["gnubg 子プロセス"]
        tls --> uv --> child
    end

    phone -- "HTTPS：アプリ本体の取得" --> static
    phone -- "HTTPS：写真・盤面の送信（CORS 許可済み）" --> tls

    classDef planned stroke-dasharray: 5 5;
    class tls planned;
```

- 写真はサーバーに送って処理するだけで、保存はしません。
- API は CORS を全オリジン許可にしているので、PWA を別ドメインから配信しても呼び出せます。

## 現状

- `recognizer/`: ステップ1の盤面認識プロトタイプ（Python / OpenCV）。詳細は [recognizer/README.md](recognizer/README.md)。
- `analyzer/`: ステップ2の局面解析 API（GNU Backgammon / FastAPI）と、ステップ3の PWA（`analyzer/static/`、`/` で配信）。詳細は [analyzer/README.md](analyzer/README.md)。
- `Dockerfile`: API と PWA を1つのコンテナで動かす。
- `samples/`: 精度確認用の写真・アプリ画面と正解データ（`*.truth.json`）。
- `docs/HANDOVER.md`: 別アカウントの Claude プロジェクトと共同で開発するための手順と、今の状況。

## 予定

1. 盤面認識の試作（済）
2. gnubg による解析（サーバー側）（済）
3. PWA（撮影・四隅指定・手修正）（済）
4. 実写真での調整
