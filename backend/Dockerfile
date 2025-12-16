# Dockerfile de producción

# Stage 1: Builder - compilar pycairo
FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    pkg-config \
    libcairo2-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Stage 2: Runtime
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    libcairo2 \
    fonts-roboto \
    fontconfig \
    && fc-cache -f -v \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Usuario no-root (requisito gobierno)
RUN groupadd -r epidemiologia && useradd -r -g epidemiologia epidemiologia

WORKDIR /app

COPY --from=builder --chown=epidemiologia:epidemiologia /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production

COPY --chown=epidemiologia:epidemiologia pyproject.toml uv.lock ./
COPY --chown=epidemiologia:epidemiologia app/ ./app/
COPY --chown=epidemiologia:epidemiologia alembic/ ./alembic/
COPY --chown=epidemiologia:epidemiologia alembic.ini ./

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

RUN mkdir -p /app/uploads /app/logs /app/.cache/seeds \
    && chown -R epidemiologia:epidemiologia /app/uploads /app/logs /app/.cache/seeds

RUN rm /bin/uv

EXPOSE 8000

USER epidemiologia

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
