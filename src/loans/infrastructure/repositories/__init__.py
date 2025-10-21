"""Repository implementations for the domain boundaries."""

from .in_memory_applications import InMemoryLoanApplicationRepository
from .postgres_applications import PostgresLoanApplicationRepository

__all__ = [
    "InMemoryLoanApplicationRepository",
    "PostgresLoanApplicationRepository",
]
