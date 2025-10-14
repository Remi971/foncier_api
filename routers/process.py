# from fastapi import APIRouter, HTTPException, Body, Depends, BackgroundTasks, status
# from dto.process import  PotentielParamsDto
# from sqlalchemy.orm import Session
# from sqlalchemy.sql import text
# from dependencies import EngineDb, oauth2_scheme
# import geopandas as gpd
# import pandas as pd
# from services.process import envelop_creation, potentiel_calcul
# from dto.process import EnveloppeParamsDto
# from models.notification import Notification as NotificationsModel
# from schema.notifications import Notifications
# from dto.notifications import NotificationsStatusEnum, NotificationsTypeEnum, NotificationsState
# from services.notifications import Notifiyer
# from services.auth import credentials
# from dto.database import DatabaseTypeEnum

# router = APIRouter(
#     prefix="/process"
# )

# #TODO : user send inputs (enveloppe layer, or params for creating enveloppe layer) AND potentiel params

# def getDb():
#     database = EngineDb(DatabaseTypeEnum.POSTGRESQL).getSession()
#     try:
#         yield database
#     finally:
#         database.close()
        
# def getDbSqlite():
#     database = EngineDb(DatabaseTypeEnum.SQLITE).getSession()
#     try:
#         yield database
#     finally:
#         database.close()
    
# @router.post('/potentiel', tags=["Processing"], summary="Calculate the potentiel available into the envelop")
# def process_potentiel(
#     background_tasks: BackgroundTasks,
#     token: str = Depends(oauth2_scheme),
#     body: PotentielParamsDto = Body,
#     db_psql: Session = Depends(getDb),
#     db: Session = Depends(getDbSqlite)
#     ):
#     try:
#         token_data = credentials(token)
#         newNotif : Notifications = {
#                 "message": "Acquisition des données terminée",
#                 "status": NotificationsStatusEnum.PENDING,
#                 "type": NotificationsTypeEnum.POTENTIEL,
#                 "recipient": token_data.id
#             }
#         notification = Notifiyer(state=NotificationsState.CREATION, db=db_psql, notif=newNotif, id=None )
#         notifId = notification.action()
#         background_tasks.add_task(potentiel_calcul, body, db, db_psql, notifId)
#         return "Caclcul du Potentiel"
#     except Exception as error:
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{error}")
    
    
# @router.post('/enveloppe', tags=["Processing"], summary="Calculate the urban envelop of the city")
# def process_envelop(
#     background_tasks: BackgroundTasks,
#     token: str = Depends(oauth2_scheme),
#     body: EnveloppeParamsDto = Body,
#     db_psql: Session = Depends(getDb),
#     db: Session = Depends(getDbSqlite)
# ):
#     try:
#         token_data = credentials(token)
#         newNotif: NotificationsModel = {
#             "message": "Calcul de l'enveloppe en cours",
#             "status": NotificationsStatusEnum.PENDING,
#             "type": NotificationsTypeEnum.ENVELOPPE,
#             "recipient": token_data.id
#         }
#         notification = Notifiyer(state=NotificationsState.CREATION, db=db_psql, notif=newNotif, id=None)
#         notifId = notification.action()
#         background_tasks.add_task(envelop_creation, body, db, db_psql, notifId)
#         return "Creating Enveloppe"
#     except Exception as error:
#         raise HTTPException(status_code=500, detail=f"{error}")
    
# # @router.put('/enveloppe', tags=["Processing"], summary="")
# # def update_enveloppe():
# #     ...
    
