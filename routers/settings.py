from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import AppSetting
from routers.admin_users import require_admin
from schemas import DEFAULT_MAINTENANCE_MESSAGE, MaintenanceSetting, MaintenanceUpdate

router = APIRouter()

MAINTENANCE_KEY = "maintenance"


async def get_maintenance(db: AsyncSession) -> MaintenanceSetting:
    row = await db.get(AppSetting, MAINTENANCE_KEY)
    if not row:
        return MaintenanceSetting()
    value = row.value or {}
    return MaintenanceSetting(
        enabled=bool(value.get("enabled")),
        message=value.get("message") or DEFAULT_MAINTENANCE_MESSAGE,
        updated_at=row.updated_at,
    )


@router.get("/maintenance", response_model=MaintenanceSetting)
async def read_maintenance(response: Response, db: AsyncSession = Depends(get_db)):
    """État du mode maintenance (public : lu par le site avant d'afficher les pages)."""
    response.headers["Cache-Control"] = "no-store"
    return await get_maintenance(db)


@router.put("/maintenance", response_model=MaintenanceSetting, dependencies=[Depends(require_admin)])
async def update_maintenance(data: MaintenanceUpdate, db: AsyncSession = Depends(get_db)):
    row = await db.get(AppSetting, MAINTENANCE_KEY)
    current = (row.value if row else None) or {}
    value = {
        "enabled": data.enabled,
        "message": (data.message or "").strip() or current.get("message") or DEFAULT_MAINTENANCE_MESSAGE,
    }
    if row:
        row.value = value
    else:
        row = AppSetting(key=MAINTENANCE_KEY, value=value)
        db.add(row)
    await db.commit()
    await db.refresh(row)  # updated_at est calculé par la base
    return await get_maintenance(db)
