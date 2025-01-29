from fastapi import APIRouter, Path, Depends, BackgroundTasks, status, HTTPException, Body
from services.data import get_data, check_data, clean_data
from services.auth import credentials
from services.notifications import Notifiyer
from dependencies import oauth2_scheme
from schema.notifications import NotificationsModel
from schema.data import CommuneDto
from dto.notifications import NotificationsStatusEnum, NotificationsTypeEnum, NotificationsState
from sqlalchemy.orm import Session
from dependencies import get_pg_db, get_db
from typing import List
from models.data import CommuneInfo

router = APIRouter(
    prefix="/data"
)

@router.post('/add/sqlite', tags=["Data"], summary="Get The PCI-Vector Data", status_code=status.HTTP_202_ACCEPTED)
def adding_data_to_db(
    background_tasks: BackgroundTasks,
    body: CommuneDto= Body(),
    token: str = Depends(oauth2_scheme),
    db_psql: Session = Depends(get_pg_db),
    db: Session = Depends(get_db),
    ):
    try:
        token_data = credentials(token)
        #TODO: Indiquer dans la base de donnée qu'un traitement est en cours
        newNotif: NotificationsModel = {
            "message": "L'acquisition des données est en cours",
            "status": NotificationsStatusEnum.PENDING,
            "type": NotificationsTypeEnum.DATA,
            "recipient": token_data.id
        }
        notification = Notifiyer(state=NotificationsState.CREATION, db=db_psql, notif=newNotif, id=None)
        notifId = notification.action()
        background_tasks.add_task(get_data,body, notifId,db_psql, db)
        return {"message": "Acquisition des données en cours"}
    except Exception as error:
        print(body)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'{error}')
    
@router.get('/', tags=["Data"])
def checkData(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    token_data = credentials(token)
    return check_data(db)

@router.delete('/', tags=["Data"])
def cleanDatabase(
    background_tasks: BackgroundTasks,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    token_data = credentials(token)
    background_tasks.add_task(clean_data,db)
    return {"message", "La base de données local est en cours de nettoyage."}
