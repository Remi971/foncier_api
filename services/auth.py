from schema.users import Users
from fastapi import Depends, HTTPException, status
import jwt
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from dependencies import oauth2_scheme
from datetime import datetime, timedelta, timezone
from schema.auth import TokenData
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN_SECRET = os.getenv("TOKEN_SECRET")
TOKEN_ALGORITHM = os.getenv("TOKEN_ALGORITHM")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def decode_token(token):
    #return user info
    info = jwt.decode(token, TOKEN_SECRET, algorithms=[TOKEN_ALGORITHM])
    return info
    
def verify_password(plain_password: str, hash_password: str):
    return pwd_context.verify(plain_password, hash_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def credentials(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, TOKEN_SECRET, algorithms=[TOKEN_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
        return token_data
    except InvalidTokenError:
        raise credentials_exception


def create_access_token(data: None, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, TOKEN_SECRET, algorithm=TOKEN_ALGORITHM)
    return encoded_jwt