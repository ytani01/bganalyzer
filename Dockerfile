# 解析サーバーと PWA を1つのコンテナで動かす。
#   docker build -t bganalyzer .
#   docker run --rm -p 8000:8000 bganalyzer     # → http://localhost:8000/
FROM python:3.12-slim-bookworm

# gnubg の拡張モジュールが glib を使う
RUN apt-get update && apt-get install -y --no-install-recommends libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY analyzer/requirements.txt analyzer/requirements.txt
RUN pip install --no-cache-dir -r analyzer/requirements.txt

COPY recognizer/ recognizer/
COPY analyzer/ analyzer/

EXPOSE 8000
# gnubg はメインスレッド以外で評価すると落ちるので、ワーカーは1つ・--reload なし
CMD ["uvicorn", "app:app", "--app-dir", "analyzer", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
