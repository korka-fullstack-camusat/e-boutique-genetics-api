from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from database import get_db
from models import Survey
from schemas import SurveyCreate, SurveyResponse

router = APIRouter()


@router.get("/surveys/", response_model=List[SurveyResponse])
async def get_all_surveys(db: AsyncSession = Depends(get_db)):
    """Lister tous les sondages (admin)"""
    result = await db.execute(select(Survey).order_by(Survey.created_at.desc()))
    return result.scalars().all()


@router.post("/surveys/", response_model=SurveyResponse, status_code=status.HTTP_201_CREATED)
async def create_survey(survey: SurveyCreate, db: AsyncSession = Depends(get_db)):
    """Créer un nouveau sondage (client)"""
    db_survey = Survey(**survey.model_dump())
    db.add(db_survey)
    await db.commit()
    await db.refresh(db_survey)
    return db_survey


@router.get("/surveys/{survey_id}", response_model=SurveyResponse)
async def get_survey_by_id(survey_id: int, db: AsyncSession = Depends(get_db)):
    """Récupérer un sondage par ID"""
    result = await db.execute(select(Survey).where(Survey.id == survey_id))
    survey = result.scalar_one_or_none()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    return survey


@router.delete("/surveys/{survey_id}")
async def delete_survey(survey_id: int, db: AsyncSession = Depends(get_db)):
    """Supprimer un sondage"""
    result = await db.execute(select(Survey).where(Survey.id == survey_id))
    survey = result.scalar_one_or_none()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    await db.delete(survey)
    await db.commit()
    return {"message": "Survey deleted"}
