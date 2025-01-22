from fastapi import APIRouter, Path, Depends, BackgroundTasks, status, HTTPException
from services.data import get_data, check_data
from services.auth import credentials
from services.notifications import Notifiyer
from dependencies import oauth2_scheme
from schema.notifications import NotificationsModel
from dto.notifications import NotificationsStatusEnum, NotificationsTypeEnum, NotificationsState
from sqlalchemy.orm import Session
from dependencies import get_pg_db, get_db

router = APIRouter(
    prefix="/data"
)

    
@router.get('/add/sqlite/{insee}', tags=["Data"], summary="Get The PCI-Vector Data", status_code=status.HTTP_202_ACCEPTED)
def adding_data_to_db(
    background_tasks: BackgroundTasks,
    token: str = Depends(oauth2_scheme),
    insee: str = Path(min_length=5, max_length=5,),
    db_psql: Session = Depends(get_pg_db),
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
        background_tasks.add_task(get_data,insee, notifId,db_psql)
        return {"message": "Acquisition des données en cours"}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'{error}')
    
@router.get('/', tags=["Data"])
def checkData(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    token_data = credentials(token)
    return check_data(db)
