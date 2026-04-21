from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.checkout import router as checkout_router
from src.db import init_db
from src.webhooks import router as webhooks_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Stripe Integration Reference",
    description="Minimal reference for Stripe Checkout + webhooks with idempotency.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(checkout_router)
app.include_router(webhooks_router)


@app.get("/")
def root():
    return {"status": "ok", "service": "stripe-integration-reference"}


@app.get("/health")
def health():
    return {"status": "healthy"}
