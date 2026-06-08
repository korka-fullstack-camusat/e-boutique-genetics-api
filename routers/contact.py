from fastapi import APIRouter, BackgroundTasks
from schemas import DevisCreate
from email_service import send_devis_notification

router = APIRouter()


@router.post("/devis", status_code=202)
async def submit_devis(data: DevisCreate, background_tasks: BackgroundTasks):
    """Reçoit une demande de devis et envoie les emails de notification."""
    background_tasks.add_task(send_devis_notification, data.model_dump())
    return {"message": "Demande de devis envoyée avec succès"}
