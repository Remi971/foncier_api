from fastapi import FastAPI, Path, Form, Body, Query, Depends, HTTPException, status, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dependencies import oauth2_scheme, EngineDb, env
from routers import users, notifications, orchestrate, data
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from schema.auth import Token
from services.user import authenticate_user, create_user
from services.auth import create_access_token, credentials
from datetime import timedelta
from pydantic import EmailStr
from dto.database import DatabaseTypeEnum
from models import Base
origins = env.BASE_URL.split(",")

database = EngineDb(DatabaseTypeEnum.POSTGRESQL)


@asynccontextmanager
async def init_db(app: FastAPI):
    print("##### init_db #####")
    Base.metadata.create_all(bind=database.engine)
    print("##### DB Created #####")
    yield

app = FastAPI(
    title="CartoFoncier",
    description="CartoFoncier API - Permet de télécharger la dernière version des données cadastrales du PCI-vecteur avec lesquelles sera calculer l'enveloppe urbaine ainsi que le potentiel foncier composé de parcelles nues et de division parcellaire. ",
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

app.include_router(users.router)
app.include_router(notifications.router)
app.include_router(orchestrate.router)
app.include_router(data.router)
   
@app.get("/health", tags=["Root"])
def health_check():
    return {"message": "Welcome to CartoFoncier API!"}

@app.post('/token',  tags=['authentication'], summary="Login")
def login(form_login : OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)) -> Token:
    print("Form login : ", form_login.username, form_login.password)
    user = authenticate_user(db, form_login.username, form_login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=float(env.ACCESS_TOKEN_EXPIRE_MINUTES))
    token = create_access_token(
        data={"sub": user.email, "id": str(user.id) }, expires_delta=access_token_expires
    )
    return Token(access_token=token["access_token"], refresh_token=token["refresh_token"], token_type="bearer")

@app.post('/signin', tags=['authentication'], summary="Sign in")
def signin(
    firstname: str = Form(),
    lastname: str = Form(),
    username: str = Form(),
    password: str = Form(),
    db: Session = Depends(database.get_db)) -> Token:
    user = create_user({
        "firstname": firstname, 
        "lastname": lastname,
        "email": username,
        "password": password
        }, db)
    access_token_expires = timedelta(minutes=float(env.ACCESS_TOKEN_EXPIRE_MINUTES))
    token = create_access_token(
        data={"sub": user.email, "id": str(user.id)}, expires_delta=access_token_expires
    )
    return Token(access_token=token["access_token"], refresh_token=token["refresh_token"], token_type="bearer")
        

@app.post('/refresh_token', tags=['authentication'], summary="Refresh Token")
def refresh_token(refresh_token : str = Depends(oauth2_scheme)):
    token = credentials(refresh_token)
    access_token_expires = timedelta(minutes=float(env.ACCESS_TOKEN_EXPIRE_MINUTES))
    token = create_access_token(
        data={"sub": token.email, "id": str(token.id)}, expires_delta=access_token_expires
    )
    return Token(access_token=token["access_token"], refresh_token=token["refresh_token"], token_type="bearer")

@app.get('/user/me', tags=['authentication'], summary="Get current user")
def read_users_me(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    token_data = credentials(token) 
    return {"email": token_data.email, "id": token_data.id}

@app.post('/reset_password',  tags=['authentication'], summary="Reset password")
def reset_password(email: EmailStr):
    ...
    
