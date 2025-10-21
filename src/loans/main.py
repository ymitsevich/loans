"""Application bootstrap for the loans microservice."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .interfaces.http.dependencies import shutdown_container
from .interfaces.http.routes import register_routes
from .utils.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await shutdown_container()


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    configure_logging()
    app = FastAPI(title="Loans Service", version="0.1.0", lifespan=lifespan)
    register_routes(app)
    return app


app = create_app()
