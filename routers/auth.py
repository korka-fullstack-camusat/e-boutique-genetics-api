import os
import hashlib

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from dotenv import load_dotenv

from schemas import LoginRequest, LoginResponse
from database import get_db
from models import AdminUser

load_dotenv()

router = APIRouter()

_ENV_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
_ENV_PWD   = os.getenv("ADMIN_PASSWORD", "admin123")
_SECRET    = os.getenv("SECRET_KEY", "secret")


def _env_token() -> str:
    """Token for the .env super-admin (backward-compat)."""
    return hashlib.sha256(f"{_ENV_EMAIL}-{_ENV_PWD}".encode()).hexdigest()


def _db_token(email: str, password_hash: str) -> str:
    return hashlib.sha256(f"{email}:{password_hash}".encode()).hexdigest()


def _hash_pwd(password: str) -> str:
    return hashlib.sha256(f"{password}{_SECRET}".encode()).hexdigest()


@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    # 1. Check .env super-admin
    if credentials.email == _ENV_EMAIL and credentials.password == _ENV_PWD:
        return LoginResponse(
            success=True,
            message="Login successful",
            user={
                "email": _ENV_EMAIL,
                "name": "Super Admin",
                "token": _env_token(),
                "role": "superadmin",
            },
        )

    # 2. Check DB admins
    result = await db.execute(
        select(AdminUser).where(
            AdminUser.email == credentials.email,
            AdminUser.is_active == True,
        )
    )
    admin = result.scalar_one_or_none()
    if admin and admin.password_hash == _hash_pwd(credentials.password):
        return LoginResponse(
            success=True,
            message="Login successful",
            user={
                "email": admin.email,
                "name": admin.name,
                "token": _db_token(admin.email, admin.password_hash),
                "role": admin.role,
            },
        )

    raise HTTPException(status_code=401, detail="Invalid credentials")
