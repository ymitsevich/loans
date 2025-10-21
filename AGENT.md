# Loans Microservice Agent Guidelines

These guardrails target a Python-first, Docker-native workflow for the `loans` microservice. Follow them to keep the codebase maintainable, testable, and production-ready.

## Python Runtime & Environment
- Pin to the latest stable Python 3 release; define it in `.python-version`, `pyproject.toml`, and Docker images.
- Use `poetry` or `pip-tools` for deterministic dependency management; track hashes and lock files.
- Enforce type checking (mypy/pyright), linting (ruff/flake8), formatting (black/ruff fmt), and security scans (bandit, pip-audit) in CI and pre-commit hooks.
- Prefer environment variables for configuration; centralize parsing with `pydantic` or similar settings management.
- Keep secrets out of the repo; load via `.env` or secret managers.

## Clean Code Practices
- Adopt PEP 8 styling plus `ruff` opinions; keep functions small with single responsibilities.
- Name modules, classes, and functions descriptively; avoid magic numbers and duplicated logic.
- Always annotate public APIs with type hints; enable `from __future__ import annotations` as needed.
- Favor composition over inheritance unless a real hierarchy exists.
- Document intent with succinct docstrings where behavior or contracts are non-obvious.
- Prefer guard clauses and early returns; avoid deep or branching `if`/`elif`/`else` chains unless a ternary keeps the flow clear.

## Clean Architecture Layout
- Keep the domain model pure Python, framework-agnostic, and free from I/O.
- Separate layers explicitly:
  - **Domain**: entities, value objects, domain services, business rules.
  - **Application/Use Case**: orchestrates domain logic, coordinates repositories, publishes events.
  - **Adapters/Interfaces**: HTTP controllers (FastAPI), CLI, message handlers.
  - **Infrastructure**: persistence, external APIs, message brokers, frameworks.
- Depend inward only; use interfaces/abstract base classes for boundary crossing.
- Treat DTOs/serializers as translation layers to protect domain purity.
- Keep framework code thin; resist leaking FastAPI/ORM constructs into the domain.

## SOLID & OOP Guidance
- **S**ingle Responsibility: each class/module handles one reason to change.
- **O**pen/Closed: add behavior through extension (strategy, policy objects) rather than modification.
- **L**iskov: honor substitution; keep method contracts consistent.
- **I**nterface Segregation: prefer small protocols or ABCs so consumers depend only on what they use.
- **D**ependency Inversion: depend on abstractions defined in stable layers; inject implementations at composition roots (e.g., FastAPI startup).

## Docker-First Workflow
- Treat Docker as the canonical execution environment; run dev, tests, and CI inside containers.
- Use multi-stage builds: builder installs dependencies and runs tests; final stage copies only runtime artifacts.
- Start from slim base images (e.g., `python:3.x-slim`); install OS deps minimally; remove build caches.
- Create a non-root user in the runtime stage and drop privileges.
- Copy only the necessary project files to leverage build caching (install dependencies before source when possible).
- Pin dependencies in the image (e.g., `pip install --no-cache-dir -r requirements.txt`); avoid `latest` tags in FROM.
- Enable Docker healthchecks that exercise readiness endpoints or lightweight probes.

## Docker Compose Conventions
- Define `docker-compose.yml` for local orchestration; keep production overrides (`docker-compose.prod.yml`) separate.
- Use named volumes for persistence and tmpfs for ephemeral caches; avoid binding secrets into images.
- Configure services with `.env` files referenced via `env_file`; never bake secrets into compose YAML.
- Wire dependencies (database, message broker) with explicit healthcheck-based startup ordering.
- Keep compose services stateless where possible; manage stateful dependencies externally or with volume-backed data directories.

## Testing & Quality Gates
- Follow the testing pyramid: fast unit tests (domain), service/integration tests (adapters), contract/API tests.
- Use `pytest` fixtures to isolate side effects; mock boundaries via interface contracts.
- Enforce 90%+ coverage on domain and application layers; monitor mutation coverage for critical modules.
- Run lint, type check, tests, and security scans in CI; block merges on failures.

## Observability & Operations
- Structure logs as JSON with request IDs/correlation IDs; ensure log levels are configurable.
- Export metrics (Prometheus) for key business and technical signals; add health/readiness endpoints.
- Capture traces (OpenTelemetry) for HTTP handlers and critical workflows; propagate context across services.
- Surface feature flags, circuit breakers, and timeouts for all external calls.

## Security & Compliance
- Validate all inputs at boundaries with schemas (FastAPI models, domain validators).
- Sanitize and parameterize all database queries; rely on the ORM or query builders to prevent injection.
- Rotate secrets regularly; integrate with secret stores (Vault, AWS Secrets Manager, etc.).
- Enable HTTPS in all environments; manage TLS termination at ingress/load balancer.

## Collaboration & Delivery
- Follow trunk-based development with short-lived branches; practice continuous delivery.
- Keep PRs small, focused, and well-described; include test evidence and architecture notes.
- Write ADRs for significant design decisions and link them in relevant modules.
- Automate migrations (Alembic) and run them inside containers as part of deployment.
- Monitor technical debt via issues board; schedule regular refactoring sprints.

Adhering to these practices keeps the `loans` microservice modular, testable, and ready for scale while preserving clarity for future contributors.
