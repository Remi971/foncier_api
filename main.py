from fastapi import FastAPI, Path, Body, Query, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dependencies import oauth2_scheme, engine_pgsql, get_pg_db, settings
from routers import data, process, users
from models.users import Base
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from schema.auth import Token
from schema.users import Users_create
from services.user import authenticate_user, create_user
from services.auth import create_access_token, credentials
from datetime import timedelta
from pydantic import EmailStr

@asynccontextmanager
async def init_db(app: FastAPI):
    print("##### init_db #####")
    Base.metadata.create_all(bind=engine_pgsql)
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