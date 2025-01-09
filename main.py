from fastapi import FastAPI, Path, Body, Query, Depends, HTTPException, status, WebSocket, WebSocketException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dependencies import oauth2_scheme, engine_pgsql, get_pg_db, settings
from routers import data, process, users
from models.users import Base as BaseUsers
from models.notification import Base as BaseNotifications
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from schema.auth import Token
from schema.users import Users_create
from services.user import authenticate_user, create_user
from services.auth import create_access_token, credentials
from datetime import timedelta
from pydantic import EmailStr
#TEST
from schema.notifications import Notifications, NotificationsMessage
from services.notifications import Notifiyer, get_last_notif
from dto.notifications import NotificationsState, NotificationsStatusEnum, NotificationsTypeEnum

@asynccontextmanager
async def init_db(app: FastAPI):
    print("##### init_db #####")
    BaseUsers.metadata.create_all(bind=engine_pgsql)
    BaseNotifications.metadata.create_all(bind=engine_pgsql)
    yield
    
origins = [
    settings.BASE_URL
]

app = FastAPI(
    title="CartoFoncier",
    description="CartoFoncier API",
    version="0.0.1",
    lifespan=init_db
    )
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
    
)
app.include_router(data.router)
app.include_router(process.router)
app.include_router(users.router)

@app.post('/token',  tags=['authentication'], summary="Login")
def login(form_login : OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_pg_db)) -> Token:
    user = authenticate_user(db, form_login.username, form_login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": user.email, "id": str(user.id) }, expires_delta=access_token_expires
    )
    return Token(access_token=token["access_token"], refresh_token=token["refresh_token"], token_type="bearer")

@app.post('/signin', tags=['authentication'], summary="Sign in")
def signin(body: Users_create = Body, db: Session = Depends(get_pg_db)) -> Token:
    user = create_user(body, db)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": user.email, "id": str(user.id)}, expires_delta=access_token_expires
    )
    return Token(access_token=token["access_token"], refresh_token=token["refresh_token"], token_type="bearer")

@app.post('/refresh_token', tags=['authentication'], summary="Refresh Token")
def refresh_token(refresh_token : str = Depends(oauth2_scheme)):
    token = credentials(refresh_token)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": token.email, "id": str(token.id)}, expires_delta=access_token_expires
    )
    return Token(access_token=token["access_token"], refresh_token=token["refresh_token"], token_type="bearer")
    
@app.post('/reset_password',  tags=['authentication'], summary="Reset password")
def reset_password(email: EmailStr):
    ...
    
#TODO : protect the websocket endpoints
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str, db: Session = Depends(get_pg_db)):
    token_data = credentials(token)
    await websocket.accept()
    while True:
        try:
            #TODO: function that check the state of last notifications - après 5min si status pending update en error
            data = await websocket.receive_text()
            print(data)
            # last_notif = get_last_notif(db)
            # print("Last Notif", last_notif)
            await websocket.send_json({"id": "id", "message": "blabla", "recipient": token_data.id, "type": "test", "status": "success"})
        except Exception as error:
            print("websocket error", error)
            raise WebSocketException(code=status.WS_1011_INTERNAL_ERROR, reason="Websocket Error")
        
@app.websocket("/ws/processing")
async def processing(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        #TODO : check dans la base de donnée si process en cours
        check = True
        if check:
            await websocket.send_text("Process en cours")
        else:
            await websocket.sen_text("Process terminé")
        
@app.post('/test_notification', tags=['TEST'])
def notifyerTest(
    token : str = Depends(oauth2_scheme),
    db: Session = Depends(get_pg_db)
):
    try:
        token_data = credentials(token)
        notif: Notifications = {
            "message": "notification Test",
            "recipient": token_data.id,
            "status": NotificationsStatusEnum.PENDING,
            "type": NotificationsTypeEnum.DATA
        }
        notify = Notifiyer(db=db, state=NotificationsState.CREATION, notif=notif, id=None )
        notifId = notify.action()
        updateNotif: Notifications = {
            "message": "update Notification Test",
            "recipient":  token_data.id,
            "status": NotificationsStatusEnum.SUCCESS,
            "type": NotificationsTypeEnum.DATA
        }
        
        updateNotify = Notifiyer(db=db, state=NotificationsState.UPDATE, notif=updateNotif, id=notifId )
        return updateNotify.action()
        
    except Exception as error:
        raise error
    
@app.delete("/notif/{id}", tags=["TEST"])
def deleteNotif(
    id: str = Path,
    db: Session = Depends(get_pg_db),
    token: str = Depends(oauth2_scheme), 
):
    token_data = credentials(token)
    notif = Notifiyer(state=NotificationsState.DELETE, db=db, notif=None, id=id)
    delete = notif.action()
    return delete
    