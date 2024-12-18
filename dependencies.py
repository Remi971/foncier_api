from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.event import listen
from geoalchemy2 import load_spatialite
from fastapi.security import OAuth2PasswordBearer
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL_SQLITE = os.getenv("DATABASE_URL_SQLITE")
engine = create_engine(DATABASE_URL_SQLITE)
listen(engine, "connect", load_spatialite)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

DATABASE_URL_POSTGRES = os.getenv("DATABASE_URL_POSTGRES")
engine_pgsql = create_engine(DATABASE_URL_POSTGRES)
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
