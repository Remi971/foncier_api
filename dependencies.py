from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.event import listen
from geoalchemy2 import load_spatialite
from fastapi.security import OAuth2PasswordBearer
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env.development', env_file_encoding='utf-8')
    DATABASE_URL_SQLITE: str
    DATABASE_URL_POSTGRES: str
    TOKEN_ALGORITHM: str
    TOKEN_SECRET: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    
        
settings = Settings()
engine = create_engine(settings.DATABASE_URL_SQLITE)
listen(engine, "connect", load_spatialite)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

engine_pgsql = create_engine(settings.DATABASE_URL_POSTGRES)
SessionLocalPgsql = sessionmaker(autocommit=False, autoflush=False, bind=engine_pgsql)

# Dependency to get the database session
def get_db():
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()
        
def get_engine():
    yield engine


def get_pg_db():
    database = SessionLocalPgsql()
    try:
        yield database
    finally:
        database.close()
        
# Security
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")        
