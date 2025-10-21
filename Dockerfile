FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /app


FROM base AS builder

ARG INSTALL_DEV="false"

RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip && pip install poetry "poetry-plugin-export"

COPY pyproject.toml .

RUN poetry export --without-hashes --format=requirements.txt --output requirements.txt \
    && if [ "$INSTALL_DEV" = "true" ]; then \
        poetry export --without-hashes --format=requirements.txt --output requirements-dev.txt --with dev; \
    fi

# Install runtime dependencies in a virtual environment; optionally add dev-only requirements.
RUN python -m venv /opt/venv \
    && . /opt/venv/bin/activate \
    && pip install --no-cache-dir -r requirements.txt \
    && if [ "$INSTALL_DEV" = "true" ]; then pip install --no-cache-dir -r requirements-dev.txt; fi

COPY src ./src


FROM base AS runtime

RUN addgroup --system loans && adduser --system --ingroup loans loans
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app/src"

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app/src ./src

USER loans

EXPOSE 8000

ENTRYPOINT ["uvicorn", "loans.main:app", "--host", "0.0.0.0", "--port", "8000"]
