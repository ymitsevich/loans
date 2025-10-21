"""Repository implementations for the domain boundaries."""

from .cached_repository import CachedLoanApplicationRepository
from .in_memory_applications import InMemoryLoanApplicationRepository
from .postgres_applications import PostgresLoanApplicationRepository

__all__ = [
    "CachedLoanApplicationRepository",
    "InMemoryLoanApplicationRepository",
    "PostgresLoanApplicationRepository",
]
