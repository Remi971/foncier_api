from fastapi import Depends, APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import EmailStr
from schema.auth import Token
from services.auth import create_access_token
from sqlalchemy.orm import Session
from dependencies import get_pg_db
import os
from dotenv import load_dotenv
from datetime import timedelta
from schema.users import Users_create
from services.user import create_user, authenticate_user
router = APIRouter(
    prefix='/auth'
)

load_dotenv()

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

@router.post('/signin')
def signin(body: Users_create = Depends(), db: Session = Depends(get_pg_db)) -> Token:
    user = create_user(body, db)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")
    
    
    
@router.post('/login')
def login(form_login : OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_pg_db)) -> Token:
    user = authenticate_user(db, form_login.username, form_login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")
    
    
@router.post('/reset_password')
def reset_password(email: EmailStr):
    ...