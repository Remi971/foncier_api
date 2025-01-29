from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from dependencies import get_pg_db, oauth2_scheme
from services.auth import credentials
from services.notifications import get_last_notif

router = APIRouter(
    prefix= "/notifications"
)

@router.get("/last", tags=["Notifications"])
def get_last_notification(db: Session = Depends(get_pg_db), token: str = Depends(oauth2_scheme)):
    tokens = credentials(token)
    return get_last_notif(db, tokens.id)