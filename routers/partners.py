from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from email_service import send_partner_notification
from models import PartnerApplication
from routers.admin_users import require_admin
from schemas import (
    PartnerApplicationCreate, PartnerApplicationUpdate, PartnerApplicationResponse,
)

router = APIRouter()


def _clean(value: str | None) -> str | None:
    value = (value or "").strip()
    return value or None


@router.post("/", status_code=status.HTTP_201_CREATED)
async def submit_application(
    data: PartnerApplicationCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Formulaire public « Je suis partenaire » : enregistre la candidature et prévient l'équipe."""
    application = PartnerApplication(
        full_name        = data.full_name.strip(),
        company          = _clean(data.company),
        phone            = data.phone.strip(),
        email            = data.email.strip().lower(),
        city             = data.city.strip(),
        zones            = _clean(data.zones),
        specialties      = [s.strip() for s in data.specialties if s.strip()],
        experience_years = data.experience_years,
        team_size        = _clean(data.team_size),
        certifications   = _clean(data.certifications),
        message          = _clean(data.message),
        status           = "nouveau",
    )
    db.add(application)
    await db.commit()
    await db.refresh(application)

    background_tasks.add_task(
        send_partner_notification,
        PartnerApplicationResponse.model_validate(application).model_dump(),
    )
    return {"message": "Candidature envoyée avec succès", "id": application.id}


@router.get("/", response_model=List[PartnerApplicationResponse], dependencies=[Depends(require_admin)])
async def list_applications(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PartnerApplication).order_by(PartnerApplication.created_at.desc()))
    return result.scalars().all()


@router.patch("/{application_id}", response_model=PartnerApplicationResponse,
              dependencies=[Depends(require_admin)])
async def update_application(
    application_id: int, data: PartnerApplicationUpdate, db: AsyncSession = Depends(get_db),
):
    application = await db.get(PartnerApplication, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Candidature introuvable")
    application.status = data.status
    await db.commit()
    await db.refresh(application)
    return application


@router.delete("/{application_id}", dependencies=[Depends(require_admin)])
async def delete_application(application_id: int, db: AsyncSession = Depends(get_db)):
    application = await db.get(PartnerApplication, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Candidature introuvable")
    await db.delete(application)
    await db.commit()
    return {"message": "Candidature supprimée"}
