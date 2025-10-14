from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.event import listen
from geoalchemy2 import load_spatialite
from fastapi.security import OAuth2PasswordBearer
from dto.database import DatabaseTypeEnum
import os
from dotenv import load_dotenv
load_dotenv()

class Env:
    DATABASE_URL= os.getenv("DATABASE_URL")
    BROKER_URL = os.getenv("BROKER_URL")
    MICROSERVICE_SIG = os.getenv("MICROSERVICE_SIG")
    ENV = os.getenv("ENV")
    TOKEN_ALGORITHM = os.getenv("TOKEN_ALGORITHM")
    TOKEN_SECRET = os.getenv("TOKEN_SECRET")
    ACCESS_TOKEN_EXPIRE_MINUTE = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_MINUTES = os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES")
    BASE_URL = os.getenv("BASE_URL")
    ORCHESTRATION_URL = os.getenv("ORCHESTRATION_URL")
    
env = Env()
print(env.DATABASE_URL)

class EngineDb:
    def __init__(self, dataType: DatabaseTypeEnum):
        self.dataType = dataType
        self.engine = self.createEngine()
        self.session = self.getSession()
    
    def createEngine(self):
        match self.dataType:
            case DatabaseTypeEnum.SQLITE:
                self.engine = create_engine(env.DATABASE_URL_SQLITE)
                listen(self.engine, "connect", load_spatialite)
            case DatabaseTypeEnum.SUPABASE:
                self.engine = create_engine(env.DATABASE_URL_SUPABASE)
            case DatabaseTypeEnum.POSTGRESQL:
                self.engine = create_engine(env.DATABASE_URL)
        return self.engine
     
    def getSession(self):
        match self.dataType:
            case DatabaseTypeEnum.SQLITE:
                session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            case DatabaseTypeEnum.SUPABASE:
                session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            case DatabaseTypeEnum.POSTGRESQL:
                session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        return session
    
    def getEngine(self):
        return self.engine
    
    def get_db(self):
        database = self.session()
        try:
            yield database
        finally:
            database.close()
             
# Security
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")      
