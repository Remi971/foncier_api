from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from dependencies import EngineDb, oauth2_scheme
from services.auth import credentials
from services.notifications import get_last_notif
from dto.database import DatabaseTypeEnum

router = APIRouter(
    prefix= "/notifications"
)

def getDb():
    database = EngineDb(DatabaseTypeEnum.POSTGRESQL).getSession()
    try:
        yield database
    finally:
        database.close()
        
@router.get("/last", tags=["Notifications"])
def get_last_notification(db: Session = Depends(getDb), token: str = Depends(oauth2_scheme)):
    tokens = credentials(token)
    return get_last_notif(db, tokens.id)