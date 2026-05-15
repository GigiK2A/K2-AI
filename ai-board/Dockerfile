FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    APP_ENV=production

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv sync --frozen --no-dev

# Run as non-root for defense-in-depth (Semgrep dockerfile.security.missing-user).
# `uploads/` must be writable by the app; chown after deps are installed.
RUN groupadd --system app && useradd --system --gid app --home /app --shell /sbin/nologin app \
    && mkdir -p /app/uploads \
    && chown -R app:app /app /opt/venv
USER app

EXPOSE 8000

CMD ["python", "main.py"]
