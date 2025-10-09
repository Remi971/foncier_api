from fastapi import HTTPException, status, Depends
from schema.notifications import Notifications
from sqlalchemy.orm import Session
from models.notification import Notification as notif_model
from dto.notifications import NotificationsState
from dependencies import EngineDb

class Notifiyer:
    def __init__(self, state: NotificationsState, db: Session, notif: Notifications | None, id: str | None):
       self.state = state
       self.notif = notif
       self.db = db
       self.id = id
       
    def action(self):
        match self.state:
            case NotificationsState.CREATION:
                try:
                    new_notif = notif_model(
                        message=self.notif["message"], 
                        status=self.notif["status"].value, 
                        type=self.notif["type"].value, 
                        recipient=self.notif["recipient"]
                        )
                    self.db.add(new_notif)
                    self.db.commit()
                    self.db.refresh(new_notif)
                    return new_notif.id
                except Exception as error:
                    print("id", self.id)
                    print("notif", self.notif)
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Notifyier - CREATION - ERROR {error}")
            case NotificationsState.UPDATE:
                try:
                    notif = self.db.query(notif_model).get({"id": self.id})
                    if not notif:
                        raise HTTPException(status_code=404, detail=f"Notification not found !")
                    notif.message = self.notif["message"]
                    notif.status = self.notif["status"].value
                    notif.type = self.notif["type"].value
                    self.db.commit()
                    return notif.id
                except Exception as error:
                    print("id", self.id)
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'{error}')
            case NotificationsState.DELETE:
                try:
                    notify = self.db.query(notif_model).filter(notif_model.id == self.id)
                    if not notify.count():
                        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Notification not found')
                    print("Count", notify.count())
                    notify.delete()
                    self.db.commit()
                    return {"message": "Notification deleted"}
                except Exception as error:
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{error}")
            case _:
                print("State unknown ! ")
                return {"message": "FAILED ! "}
            
def get_last_notif(db:Session, id: str):
    try:
        return db.query(notif_model).filter_by(recipient=id).order_by(notif_model.updatedAt.desc()).first()
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{error}")
