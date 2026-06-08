from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from sqlalchemy import text

from database import engine, Base
from routers import products, orders, auth, upload, survey, contact
from routers import admin_users  # noqa: F401 — imported for side-effect (model registration)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        # Crée les tables manquantes (sans toucher aux existantes)
        await conn.run_sync(Base.metadata.create_all)

        # Ajoute les nouvelles colonnes orders si elles n'existent pas encore
        await conn.execute(text("""
            ALTER TABLE orders
                ADD COLUMN IF NOT EXISTS delivery_method VARCHAR,
                ADD COLUMN IF NOT EXISTS delivery_fee     FLOAT   DEFAULT 0,
                ADD COLUMN IF NOT EXISTS acompte_amount   FLOAT
        """))
    yield


app = FastAPI(
    title="GROUPE GENETICS E-COMMERCE API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
    lifespan=lifespan,
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router,    prefix="/api/products",     tags=["products"])
app.include_router(orders.router,      prefix="/api/orders",       tags=["orders"])
app.include_router(auth.router,        prefix="/api/auth",         tags=["auth"])
app.include_router(upload.router,      prefix="/api/upload",       tags=["upload"])
app.include_router(survey.router,      prefix="/api/survey",       tags=["survey"])
app.include_router(admin_users.router, prefix="/api/admin-users",  tags=["admin-users"])
app.include_router(contact.router,     prefix="/api/contact",       tags=["contact"])


@app.get("/")
async def read_root():
    return {"message": "GROUPE GENETICS E-COMMERCE API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
