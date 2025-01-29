from fastapi import APIRouter, HTTPException, Body, Depends, BackgroundTasks, status
from dto.process import  PotentielParamsDto
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from dependencies import get_db, get_engine, get_pg_db, oauth2_scheme
import geopandas as gpd
import pandas as pd
from services.process import envelop_creation, potentiel_calcul
from dto.process import EnveloppeParamsDto
from schema.notifications import Notifications
from dto.notifications import NotificationsStatusEnum, NotificationsTypeEnum, NotificationsState
from services.notifications import Notifiyer
from services.auth import credentials

router = APIRouter(
    prefix="/process"
)

#TODO : user send inputs (enveloppe layer, or params for creating enveloppe layer) AND potentiel params
    
@router.post('/potentiel', tags=["Processing"], summary="Register Potentiel Operation")
def process_potentiel(
    background_tasks: BackgroundTasks,
    token: str = Depends(oauth2_scheme),
    body: PotentielParamsDto = Body,
    db: Session = Depends(get_pg_db)
    ):
    try:
        token_data = credentials(token)
        newNotif : Notifications = {
                "message": "Acquisition des données terminée",
                "status": NotificationsStatusEnum.PENDING,
                "type": NotificationsTypeEnum.POTENTIEL,
                "recipient": token_data.id
            }
        notificationId = Notifiyer(state=NotificationsState.CREATION, db=db, notif=newNotif )
        background_tasks.add_task(potentiel_calcul, body, db, notificationId)
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, details=f"{error}")
    
    
@router.post('/enveloppe', tags=["Processing"])
def process_envelop(
    background_tasks: BackgroundTasks,
    token: str = Depends(oauth2_scheme),
    body: EnveloppeParamsDto = Body,
    db: Session = Depends(get_db)
):
    try:
        # token_data = credentials(token)
        background_tasks.add_task(envelop_creation, body, db)
        return "Creating Enveloppe"
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"{error}")
    
