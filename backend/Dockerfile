FROM python:3.12.12-slim
WORKDIR /app
RUN pip install --no-cache-dir uv==0.12.24
COPY pyproject.toml uv.lock ./
COPY src ./src
RUN uv sync --frozen --no-dev --no-install-project && uv sync --frozen --no-dev
COPY alembic.ini ./
COPY migrations ./migrations
COPY scripts ./scripts
CMD ["sh", "-c", "uv run --no-sync alembic upgrade head && uv run --no-sync uvicorn skill_inventory.main:app --host 0.0.0.0 --port 8000"]
