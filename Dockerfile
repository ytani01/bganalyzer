# 解析サーバーと PWA を1つのコンテナで動かす。
#   docker build -t bganalyzer .
#   docker run --rm -p 8000:8000 bganalyzer     # → http://localhost:8000/
FROM python:3.12-slim-bookworm

# gnubg の拡張モジュールが glib を使う
RUN apt-get update && apt-get install -y --no-install-recommends libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /usr/local/bin/uv

WORKDIR /app
# イメージの Python を使い、uv.lock どおりに本番用の依存だけ入れる
ENV UV_PYTHON_DOWNLOADS=never \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy
COPY pyproject.toml uv.lock .python-version ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev

COPY recognizer/ recognizer/
COPY analyzer/ analyzer/

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
# gnubg はメインスレッド以外で評価すると落ちるので、ワーカーは1つ・--reload なし
CMD ["uvicorn", "app:app", "--app-dir", "analyzer", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
