from fastapi import Depends, APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import EmailStr
from schema.auth import Token
from services.auth import create_access_token, credentials
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv
from datetime import timedelta
from schema.users import Users_create
from services.user import create_user, authenticate_user
from dependencies import env, oauth2_scheme, EngineDb
from dto.database import DatabaseTypeEnum
router = APIRouter(
    prefix='/auth'
)
def getDb():
    database = EngineDb(DatabaseTypeEnum.POSTGRESQL).getSession()
    try:
        yield database
    finally:
        database.close()

@router.post('/signin', tags=['authentication'])
def signin(body: Users_create = Depends(), db: Session = Depends(getDb)) -> Token:
    user = create_user(body, db)
    access_token_expires = timedelta(minutes=float(env.ACCESS_TOKEN_EXPIRE_MINUTES))
    token = create_access_token(
        data={"sub": user.email, "id": str(user.id)}, expires_delta=access_token_expires
    )
    return Token(access_token=token["access_token"], refresh_token=token["refresh_token"], token_type="bearer")
    
    
    
@router.post('/login',  tags=['authentication'])
def login(form_login : OAuth2PasswordRequestForm = Depends(), db: Session = Depends(getDb)) -> Token:
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
    print(token)
    return Token(access_token=token["access_token"], refresh_token=token["refresh_token"], token_type="bearer")
    
@router.post('/refresh_token', tags=['authentication'])
def refresh_token(refresh_token : str = Depends(oauth2_scheme)):
    token = credentials(refresh_token)
    
@router.post('/reset_password',  tags=['authentication'])
def reset_password(email: EmailStr):
    ...