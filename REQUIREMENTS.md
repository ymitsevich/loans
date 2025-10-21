# Loan Application Processing Service Requirements

## Scope

A FastAPI-based microservice that collects loan applications, publishes them to Kafka, processes decisions asynchronously, stores results in PostgreSQL, and exposes the latest status through a REST API with a Redis cache for fast reads. The focus is on clean architecture, clear separation of concerns, and reasoning about design trade-offs.

## Architecture Guidelines

- Clean Architecture layering (domain, use cases, interfaces/adapters, infrastructure).
- SOLID principles so components stay cohesive and extensible.
- Asynchronous FastAPI endpoints.
- Explicit dependency management (e.g., FastAPI `Depends`, DI container).
- Structure and clarity over exhaustive feature completeness.

## REST API

1. **POST `/application`**
   ```json
   {
     "applicant_id": "string",
     "amount": 1000,
     "term_months": 12
   }
   ```
   - Validates the request and publishes the loan application event to Kafka.

2. **GET `/application/{applicant_id}`**
   - Returns the latest application status, reading from Redis when available and falling back to PostgreSQL otherwise.

## Kafka Processing Workflow

- Validate message payloads (`amount` > 0, `term_months` between 1 and 60).
- Determine status (`approved` or `rejected`) using the configured amount threshold.
- Persist results in PostgreSQL via SQLAlchemy/SQLModel.
- Cache the status in Redis with a 1-hour TTL.

## Suggested Tech Stack

- Python 3.11+
- FastAPI
- SQLAlchemy or SQLModel
- PostgreSQL (or MySQL alternative)
- Kafka (aiokafka or confluent-kafka)
- Redis (redis.asyncio or aioredis)
- Docker / Docker Compose (optional but recommended for local orchestration)

## Quality Expectations

- Maintains a clear separation between domain logic, use cases, interfaces, and infrastructure.
- Keeps the codebase readable and well-organised.
- Includes basic unit or integration tests where they add value.

## Future Enhancements

- Implement a transactional outbox or retry strategy to keep PostgreSQL and Kafka operations in sync.
- Add a Dead-Letter Queue (DLQ) or retry policy for the Kafka processor.
- Expand contract/integration tests for the real Redis and Kafka adapters.
- Introduce authentication/authorization and rate limiting for the API.
- Manage secrets per environment (avoid relying on `.env` defaults outside local development).
- Adopt Alembic migrations once the schema evolves beyond the initial scope.
- Extend observability (dashboards, alerts, trace IDs, processor health endpoints).
- Consider supporting multiple concurrent applications per applicant (introduce an `application_id`).
