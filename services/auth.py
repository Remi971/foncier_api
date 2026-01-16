from schema.users import Users
from fastapi import Depends, HTTPException, status
import jwt
from jwt.exceptions import InvalidTokenError
# from passlib.context import CryptContext
import bcrypt
from dependencies import oauth2_scheme
from datetime import datetime, timedelta, timezone
from schema.auth import TokenData
from dependencies import env

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def decode_token(token):
    #return user info
    info = jwt.decode(token, env.TOKEN_SECRET, algorithms=[env.TOKEN_ALGORITHM])
    return info
    
def verify_password(plain_password: str, hash_password: str):
    password_byte_enc = plain_password.encode('utf-8')
    hash_password_byte_enc = hash_password.encode('utf-8')
    return bcrypt.checkpw(password = password_byte_enc , hashed_password = hash_password_byte_enc)

def get_password_hash(password):
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
    string_password = hashed_password.decode('utf8')
    return string_password

def credentials(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, env.TOKEN_SECRET, algorithms=[env.TOKEN_ALGORITHM])
        email: str = payload.get("sub")
        id: str = payload.get("id")
        if email is None:
            print("email error")
            raise credentials_exception
        token_data = TokenData(email=email, id=id)
        return token_data
    except InvalidTokenError as e:
        print(f"InvalidTokenError : {e}")
        raise credentials_exception


def create_access_token(data: None, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=5.0)
    refresh_expire = datetime.now(timezone.utc) + timedelta(minutes=float(env.REFRESH_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    access_token = jwt.encode(to_encode, env.TOKEN_SECRET, algorithm=env.TOKEN_ALGORITHM)
    
    refresh_to_encode =data.copy()
    refresh_to_encode.update({"exp": refresh_expire})
    refresh_token = jwt.encode(refresh_to_encode, env.TOKEN_SECRET, algorithm=env.TOKEN_ALGORITHM)
    return {"access_token": access_token, "refresh_token": refresh_token}