from contextlib import asynccontextmanager
from fastapi import APIRouter, FastAPI

from db import close_db

from config import settings

from app.repositories import ProductRepository
from app.routers import products


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- startup logic ---
    app.state.product_repository = ProductRepository()

    yield

    # --- shutdown logic ---
    del app.state.product_repository
    close_db()


api_prefix = f"/{settings.API_NAME}/{settings.API_VERSION}"

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url=f"{api_prefix}/docs",
    redoc_url=f"{api_prefix}/redoc",
    swagger_ui_oauth2_redirect_url=f"{api_prefix}/docs/oauth2-redirect",
    openapi_url=f"{api_prefix}/openapi.json",
)


# Include routers
api = APIRouter(prefix=api_prefix)
api.include_router(products.router)
app.include_router(api)
