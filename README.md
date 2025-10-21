# Loan Application Processing Service

A lightweight FastAPI microservice for accepting loan applications, emitting them to Kafka, validating decisions asynchronously, persisting state in PostgreSQL, and caching the latest status in Redis for fast reads.

## Requirements

- Docker & Docker Compose
- GNU `make`
- Optional: Python 3.12 and [Poetry](https://python-poetry.org/) for local tooling

## Getting Started

```bash
cp .env.example .env          # adjust credentials if needed
make build                    # build images with dev tooling
make db-init                  # create PostgreSQL schema
make up                       # launch API, Kafka, Redis, Postgres, processor
make processor-logs           # tail the processor logs (Ctrl+C to exit)
```

Smoke-test the end-to-end pipeline (API → Kafka → processor → PostgreSQL/Redis):

```bash
python scripts/full_flow_check.py  # defaults to http://localhost:8000
# or set LOANS_API_BASE_URL=http://localhost:18000 when running from the host
```

Warm the Redis cache (useful after processor restarts):

```bash
docker compose exec api python scripts/warm_cache.py
```

## Make Targets

- `make build` – build container images with dev dependencies
- `make up` / `make down` – start or stop the docker-compose stack
- `make test` – run the pytest suite inside the API container
- `make lint` – run `ruff check` inside the API container
- `make db-init` – bootstrap the PostgreSQL schema
- `make processor-logs` – follow the Kafka processor output
- `make shell` – open an interactive shell inside the API container

## Observability

- Processor Prometheus metrics exposed on `${PROCESSOR_METRICS_PORT:-9000}`
- Structured JSON logs emitted by API and processor containers

## Local Development

```bash
poetry install
poetry run ruff check src tests
poetry run pytest
```

Configuration toggles (see `.env.example` for defaults):

- `REPOSITORY_BACKEND` – `postgres` or `memory`
- `CACHE_BACKEND` – `redis` or `memory`
- `PUBLISHER_BACKEND` – `kafka` or `memory`

## Documentation

- [REQUIREMENTS.md](REQUIREMENTS.md) outlines the service requirements and future enhancements.
- `AGENT.md` documents architecture guardrails and coding standards used by the project.
