# 解析サーバーと PWA を1つのコンテナで動かす。x86_64 と arm64（Raspberry Pi）の両方でビルドできる。
#   docker build -t bganalyzer .
#   docker run --rm -p 8000:8000 bganalyzer     # → http://localhost:8000/
# Raspberry Pi で公開する手順は docs/raspi.md（compose.yaml と Tailscale Funnel）。

# ---- ビルド用（依存を /app/.venv に入れる） ----
FROM python:3.12-slim-bookworm AS build

COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /usr/local/bin/uv

WORKDIR /app
# イメージの Python を使い、uv.lock どおりに本番用の依存だけ入れる
ENV UV_PYTHON_DOWNLOADS=never \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy
COPY pyproject.toml uv.lock .python-version ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev --no-install-package gnubg

# gnubg: PyPI の wheel は x86_64 用だけ（ソース配布もない）。それ以外（arm64 など）では
# PyPI の wheel の元になっているリポジトリから、uv.lock と同じ版（1.1.0a16）をビルドして入れる。
# サブモジュールの URL が ssh なので、https に読み替えて取る。
ARG GNUBG_PYPI_REPO=https://github.com/StonesAndDice/gnubg-pypi.git
ARG GNUBG_PYPI_REV=4b3596d882b7769e76e4d3b63125aaaae4afd90e
RUN --mount=type=cache,target=/root/.cache/uv \
    if [ "$(uname -m)" = x86_64 ]; then \
        uv sync --frozen --no-dev; \
    else \
        apt-get update \
        && apt-get install -y --no-install-recommends build-essential git pkg-config \
           libglib2.0-dev libreadline-dev libgmp-dev libsqlite3-dev \
        && git init -q /tmp/gnubg && cd /tmp/gnubg \
        && git fetch -q --depth 1 "$GNUBG_PYPI_REPO" "$GNUBG_PYPI_REV" && git checkout -q FETCH_HEAD \
        && git -c url."https://github.com/".insteadOf="git@github.com:" \
               submodule update -q --init --recursive --depth 1 \
        && uv build --wheel --python /usr/local/bin/python3 -o /tmp/wheels . \
        && uv pip install --python /app/.venv/bin/python /tmp/wheels/gnubg-*.whl \
        && rm -rf /tmp/gnubg /tmp/wheels /var/lib/apt/lists/*; \
    fi

# ---- 実行用 ----
FROM python:3.12-slim-bookworm

# gnubg の拡張モジュールが glib を使う（ソースからビルドしたものは readline と gmp も）
RUN apt-get update && apt-get install -y --no-install-recommends \
       libglib2.0-0 libreadline8 libgmp10 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=build /app/.venv /app/.venv
COPY recognizer/ recognizer/
COPY analyzer/ analyzer/

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
# gnubg はメインスレッド以外で評価すると落ちるので、ワーカーは1つ・--reload なし
CMD ["uvicorn", "app:app", "--app-dir", "analyzer", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
