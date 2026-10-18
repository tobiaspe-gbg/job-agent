FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libgbm1 \
    libasound2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libpango-1.0-0 libcairo2 fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY roles.yaml ./

RUN uv sync --frozen --no-dev \
    && uv run playwright install --with-deps chromium

ENV PATH="/app/.venv/bin:$PATH"
ENV JOB_AGENT_ROOT=/app
ENV DATA_DIR=data
ENV OUTBOX_DIR=outbox
ENV CV_DIR=CV

VOLUME ["/app/data", "/app/outbox", "/app/CV"]

CMD ["uv", "run", "job-agent"]
