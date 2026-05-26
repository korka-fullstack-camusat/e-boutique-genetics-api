import os
import hashlib
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import AdminUser
from schemas import AdminUserCreate, AdminUserUpdate, AdminUserResponse

router = APIRouter()

_SECRET    = os.getenv("SECRET_KEY", "secret")
_ENV_EMAIL = os.getenv("ADMIN_EMAIL", "")
_ENV_PWD   = os.getenv("ADMIN_PASSWORD", "")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _hash_pwd(password: str) -> str:
    """One-way hash for stored passwords."""
    return hashlib.sha256(f"{password}{_SECRET}".encode()).hexdigest()


def _env_token() -> str:
    """Token for the .env super-admin (keeps backward-compat with auth.py)."""
    return hashlib.sha256(f"{_ENV_EMAIL}-{_ENV_PWD}".encode()).hexdigest()


def _db_token(email: str, password_hash: str) -> str:
    return hashlib.sha256(f"{email}:{password_hash}".encode()).hexdigest()


# ── Auth dependency ───────────────────────────────────────────────────────────

async def require_admin(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> bool:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Non autorisé")

    token = authorization.split(" ", 1)[1]

    # 1. Check env super-admin
    if token == _env_token():
        return True

    # 2. Check DB admins
    result = await db.execute(
        select(AdminUser).where(AdminUser.is_active == True)
    )
    for admin in result.scalars().all():
        if token == _db_token(admin.email, admin.password_hash):
            return True

    raise HTTPException(status_code=401, detail="Token invalide")


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[AdminUserResponse])
async def list_admins(
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(require_admin),
):
    result = await db.execute(
        select(AdminUser).order_by(AdminUser.created_at.desc())
    )
    return result.scalars().all()


@router.post("/", response_model=AdminUserResponse, status_code=201)
async def create_admin(
    data: AdminUserCreate,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(require_admin),
):
    # Block duplicate emails (env + DB)
    if data.email == _ENV_EMAIL:
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")

    existing = await db.execute(
        select(AdminUser).where(AdminUser.email == data.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")

    admin = AdminUser(
        name=data.name,
        email=data.email,
        password_hash=_hash_pwd(data.password),
        role=data.role,
        is_active=True,
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    return admin


@router.patch("/{admin_id}", response_model=AdminUserResponse)
async def update_admin(
    admin_id: int,
    data: AdminUserUpdate,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(require_admin),
):
    result = await db.execute(
        select(AdminUser).where(AdminUser.id == admin_id)
    )
    admin = result.scalar_one_or_none()
    if not admin:
        raise HTTPException(status_code=404, detail="Administrateur non trouvé")

    if data.name is not None:
        admin.name = data.name
    if data.password is not None:
        admin.password_hash = _hash_pwd(data.password)
    if data.is_active is not None:
        admin.is_active = data.is_active

    await db.commit()
    await db.refresh(admin)
    return admin


@router.delete("/{admin_id}")
async def delete_admin(
    admin_id: int,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(require_admin),
):
    result = await db.execute(
        select(AdminUser).where(AdminUser.id == admin_id)
    )
    admin = result.scalar_one_or_none()
    if not admin:
        raise HTTPException(status_code=404, detail="Administrateur non trouvé")

    await db.delete(admin)
    await db.commit()
    return {"success": True}
