# bganalyzer

スマホで撮った実物のバックギャモン盤の写真から局面を読み取り、GNU Backgammon で解析する（勝率・ギャモン率・ピップ数）ためのプロジェクトです。最終的には PWA にする予定です。

図の中で点線・「予定」と書いた部分はまだ作っていません。

## 全体のソフトウェア構成

利用者のスマホで動く PWA（予定）が写真を撮り、サーバーの解析 API に送ります。サーバーは盤面認識（OpenCV）と局面解析（GNU Backgammon）を行い、結果を JSON で返します。

```mermaid
flowchart LR
    subgraph phone["スマホ（ブラウザ）"]
        pwa["PWA（予定）<br/>撮影・四隅タップ<br/>自分の色・ホーム側の指定<br/>認識結果の手修正・結果表示"]
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

    pwa -. "HTTPS / JSON・multipart（予定）" .-> api

    classDef planned stroke-dasharray: 5 5;
    class pwa planned;
```

| 層 | 場所 | 技術 | 状態 |
|---|---|---|---|
| 画面（撮影・手修正・結果表示） | スマホのブラウザ | PWA | 予定（ステップ3） |
| HTTP API | サーバー | FastAPI / uvicorn | 済（ステップ2） |
| 盤面認識 | サーバー | Python / OpenCV | 済（ステップ1） |
| 局面解析 | サーバー（子プロセス） | GNU Backgammon（gnubg） | 済（ステップ2） |

## モジュール構成

```mermaid
flowchart TB
    subgraph analyzer["analyzer/（ステップ2）"]
        app["app.py<br/>FastAPI のエンドポイント<br/>/analyze, /analyze-photo, /health"]
        analysis["analysis.py<br/>gnubg 呼び出し・確率/エクイティ整形<br/>日本語の要約"]
        worker["gnubg 子プロセス<br/>（そのメインスレッドで評価）"]
        test["test_api.py<br/>API のテスト"]
    end

    subgraph recognizer["recognizer/（ステップ1）"]
        board["board.py<br/>写真 → 盤面（認識本体）"]
        position["position.py<br/>盤面モデル・Position ID・ピップ数"]
        synth["synth.py<br/>合成画像の生成（正解付き）"]
        evaluate["evaluate.py<br/>正解と比べて精度を出す"]
    end

    samples[("samples/<br/>写真・画面と正解 *.truth.json")]

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
| `analyzer/analysis.py` | gnubg で勝率・ギャモン率・エクイティ・最善手を計算。gnubg はメインスレッド以外で落ちるので専用の子プロセスで動かす |

詳しくは [recognizer/README.md](recognizer/README.md) と [analyzer/README.md](analyzer/README.md) を見てください。

## 処理の流れ（写真から解析まで）

```mermaid
sequenceDiagram
    actor U as 利用者
    participant P as PWA（予定）
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

PWA はまだ無いので、API は `curl` などで直接呼び出します。

```mermaid
flowchart LR
    dev["開発者の PC<br/>curl / テスト"] -- "HTTP :8000" --> uv["uvicorn<br/>（ワーカー1つ・--reload なし）"]
    subgraph host["開発マシン"]
        uv --> app["app.py"]
        app --> child["gnubg 子プロセス"]
    end
```

### 予定（公開後）

ホスティング先は未定です。gnubg が子プロセスとメインスレッドを必要とするため、サーバーレス関数ではなく常駐する Python プロセス（コンテナや VPS）で動かす想定です。

```mermaid
flowchart LR
    phone["スマホ<br/>PWA（予定）"]
    static["静的ファイル配信（予定）<br/>HTML / JS / manifest / Service Worker"]
    subgraph backend["API サーバー（予定・ホスティング先は未定）"]
        tls["HTTPS 終端<br/>（リバースプロキシ等）"]
        uv["uvicorn + app.py<br/>（ワーカー1つ）"]
        child["gnubg 子プロセス"]
        tls --> uv --> child
    end

    phone -- "HTTPS：アプリ本体の取得" --> static
    phone -- "HTTPS：写真・盤面の送信（CORS 許可済み）" --> tls

    classDef planned stroke-dasharray: 5 5;
    class phone,static,tls,uv,child planned;
```

- 写真はサーバーに送って処理するだけで、保存はしません。
- API は CORS を全オリジン許可にしているので、PWA を別ドメインから配信しても呼び出せます。

## 現状

- `recognizer/`: ステップ1の盤面認識プロトタイプ（Python / OpenCV）。詳細は [recognizer/README.md](recognizer/README.md)。
- `analyzer/`: ステップ2の局面解析 API（GNU Backgammon / FastAPI）。詳細は [analyzer/README.md](analyzer/README.md)。
- `samples/`: 精度確認用の写真・アプリ画面と正解データ（`*.truth.json`）。

## 予定

1. 盤面認識の試作（済）
2. gnubg による解析（サーバー側）（済）
3. PWA（撮影・四隅指定・手修正）
4. 実写真での調整
