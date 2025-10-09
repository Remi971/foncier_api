from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from dto.process import EnveloppeParamsDto, PotentielParamsDto
from dependencies import EngineDb
from dto.data import LayerName
from dto.database import DatabaseTypeEnum
from .geoprocessing import Layer, processing_envelop, processing_potentiel
from models.notification import Notification as NotificationsModel
from dto.notifications import NotificationsTypeEnum, NotificationsState, NotificationsStatusEnum
from services.notifications import Notifiyer
from services.geoprocessing import enveloppeParamsControl, saveEnvelopInDb, potentielParamsControl, savePotentielInDb

engine = EngineDb(DatabaseTypeEnum.SQLITE).getEngine()


def envelop_creation(body: EnveloppeParamsDto, db: Session, dbpg: Session, notifId: str):
    try:
        bati = Layer(name=LayerName.BATIMENT.value, engine=engine)
        parcelle = Layer(name=LayerName.PARCELLE.value, engine=engine)
        tsurf = Layer(name=LayerName.TSURF.value, engine=engine)
        commune = Layer(name=LayerName.COMMUNE.value, engine=engine)
        voiep = Layer(name=LayerName.VOIEP.value, engine=engine)
        
        query_enveloppe = f"DELETE FROM enveloppe"
        db.execute(text(query_enveloppe))
        query_enveloppe_info = f"DELETE FROM enveloppe_info"
        db.execute(text(query_enveloppe_info))
        
        errors = enveloppeParamsControl(body)
        if len(errors):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=errors)
        
        enveloppe = processing_envelop(
            bati.gdf,
            parcelle.gdf,
            tsurf.gdf,
            commune.gdf,
            voiep.gdf,
            body,
            db,
            notifId
        )
        saveEnvelopInDb(enveloppe, db, body)
        newNotif: NotificationsModel = {
                "message": "Le calcul de l'enveloppe s'est terminé avec succès",
                "status": NotificationsStatusEnum.SUCCESS,
                "type": NotificationsTypeEnum.ENVELOPPE,
            }
        notification = Notifiyer(state=NotificationsState.UPDATE, db=dbpg, notif=newNotif, id=notifId)
        notifId = notification.action()
        return {"message": "Success"}
    except Exception as error:
        print(f"Echec du calcul de l'enveloppe : {error}")
        newNotif: NotificationsModel = {
                "message": "Le calcul de l'enveloppe a échoué",
                "status": NotificationsStatusEnum.ERROR,
                "type": NotificationsTypeEnum.ENVELOPPE,
            }
        notification = Notifiyer(state=NotificationsState.UPDATE, db=dbpg, notif=newNotif, id=notifId)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{error}")

def potentiel_calcul(
    body: PotentielParamsDto,
    db: Session,
    dbpg: Session,
    notifId: str
    ):
    try: 
        bati = Layer(name=LayerName.BATIMENT.value, engine=engine)
        parcelle = Layer(name=LayerName.PARCELLE.value, engine=engine)
        tsurf = Layer(name=LayerName.TSURF.value, engine=engine)
        enveloppe = Layer(name=LayerName.ENVELOPPE.value, engine=engine)
        voiep = Layer(name=LayerName.VOIEP.value, engine=engine)
        
        query_potentiel = f"DELETE FROM potentiel"
        db.execute(text(query_potentiel))
        query_potentiel_info = f"DELETE FROM potentiel_info"
        db.execute(text(query_potentiel_info))
        
        errors = potentielParamsControl(body)
        if len(errors):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=errors)
        #TODO : Save a layer of the potentiel in the database and create a notification of processing and remove the previous layer
        
        potentiel = processing_potentiel(
            bati.gdf,
            enveloppe.gdf,
            parcelle.gdf,
            tsurf.gdf,
            voiep.gdf,
            body
        )
        savePotentielInDb(potentiel, db, body)
        newNotif: NotificationsModel = {
                "message": "Le calcul du potentiel s'est terminé avec succès",
                "status": NotificationsStatusEnum.SUCCESS,
                "type": NotificationsTypeEnum.POTENTIEL,
            }
        notification = Notifiyer(state=NotificationsState.UPDATE, db=dbpg, notif=newNotif, id=notifId)
        notifId = notification.action()
        return {"message": "Success"}
    except Exception as error:
        newNotif: NotificationsModel = {
                "message": "Le calcul du potentiel a échoué",
                "status": NotificationsStatusEnum.ERROR,
                "type": NotificationsTypeEnum.POTENTIEL,
            }
        notification = Notifiyer(state=NotificationsState.UPDATE, db=dbpg, notif=newNotif, id=notifId)
        notifId = notification.action()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{error}")