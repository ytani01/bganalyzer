# CLAUDE.md（bganalyzer）

バックギャモン盤の写真から局面を読み取り、GNU Backgammon で解析する。
全体の構成は [README.md](README.md)、各部の詳細は
[recognizer/README.md](recognizer/README.md) と [analyzer/README.md](analyzer/README.md)。

## コマンド

```bash
pip install -r analyzer/requirements.txt
python3 -m pytest analyzer                                       # テスト
uvicorn app:app --app-dir analyzer --host 0.0.0.0 --port 8000    # API の起動
python3 recognizer/board.py <写真> --corners ... --home left|right   # 認識だけ試す
```

## 変えないもの

- **API は `--reload` や複数ワーカーで動かさない。** gnubg はメインスレッド以外で
  評価するとクラッシュするので、解析は専用の子プロセスで行っている
  （`analyzer/analysis.py`）
- **色の呼び方: white = 写真の手前のプレイヤー、black = 奥のプレイヤー。**
  `points[i]` は手前側から見たポイント i+1、正が white、負が black。
  認識と解析で揃えている
- 写真はサーバーで処理するだけで保存しない
- `samples/` の写真と正解の `*.truth.json` はリポジトリに入れて公開している
  （クラウドでも精度を確認できるように）

## 精度の確認

認識を変えたら `recognizer/evaluate.py` で `samples/*.truth.json` と比べ、
`recognizer/README.md` の「精度」の表を更新する。

## タスク管理

`TODO.md` で管理する（書式は `~/.claude/CLAUDE.md` と `todo-workflow` skill）。
