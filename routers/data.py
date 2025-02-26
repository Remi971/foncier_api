from fastapi import APIRouter, Depends, BackgroundTasks, status, HTTPException, Body
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from services.data import get_data, check_data_commune, check_data_enveloppe, check_data_potentiel, clean_data, download_potentiel_layer
from services.auth import credentials
from services.notifications import Notifiyer
from dependencies import oauth2_scheme
from schema.notifications import NotificationsModel
from schema.data import CommuneDto
from dto.notifications import NotificationsStatusEnum, NotificationsTypeEnum, NotificationsState
from sqlalchemy.orm import Session
from dependencies import get_pg_db, get_db

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
    
@router.get('/commune', tags=["Data"], summary="Get info about commune data and the geojson layer")
def checkDataCommune(
    token: str = Depends(oauth2_scheme),
):
    token_data = credentials(token)
    info = check_data_commune()
    return JSONResponse(content=jsonable_encoder(info))

@router.get('/enveloppe', tags=["Data"], summary="Get info about enveloppe data and the geojson layer")
def checkDataEnveloppe(
    token: str = Depends(oauth2_scheme),
):
    token_data = credentials(token)
    info = check_data_enveloppe()
    return JSONResponse(content=jsonable_encoder(info))

@router.get('/potentiel', tags=["Data"], summary="Get info about potentiel data and the geojson layer")
def checkDataPotentiel(
    token: str = Depends(oauth2_scheme),
):
    token_data = credentials(token)
    info = check_data_potentiel()
    return JSONResponse(content=jsonable_encoder(info))

@router.delete('/', tags=["Data"])
def cleanDatabase(
    background_tasks: BackgroundTasks,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    token_data = credentials(token)
    background_tasks.add_task(clean_data,db)
    return {"message", "La base de données local est en cours de nettoyage."}

@router.get('/potentiel/download', tags=["Data"], summary="Download potentiel geojson layer")
def downloadPotentiel(
    token: str = Depends(oauth2_scheme),
):
    token_data = credentials(token)
    return download_potentiel_layer()
    