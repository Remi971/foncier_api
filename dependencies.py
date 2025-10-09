from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.event import listen
from geoalchemy2 import load_spatialite
from fastapi.security import OAuth2PasswordBearer
from pydantic_settings import BaseSettings, SettingsConfigDict
from dto.database import DatabaseTypeEnum

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env.development', env_file_encoding='utf-8')
    DATABASE_URL_SQLITE: str
    DATABASE_URL_SUPABASE: str
    DATABASE_URL_POSTGRES: str
    TOKEN_ALGORITHM: str
    TOKEN_SECRET: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_MINUTES: int
    BASE_URL: str
    
settings = Settings()

class EngineDb:
    def __init__(self, dataType: DatabaseTypeEnum):
        self.dataType = dataType
        self.engine = self.createEngine()
        self.session = self.getSession()
    
    def createEngine(self):
        match self.dataType:
            case DatabaseTypeEnum.SQLITE:
                self.engine = create_engine(settings.DATABASE_URL_SQLITE)
                listen(self.engine, "connect", load_spatialite)
            case DatabaseTypeEnum.SUPABASE:
                self.engine = create_engine(settings.DATABASE_URL_SUPABASE)
            case DatabaseTypeEnum.POSTGRESQL:
                self.engine = create_engine(settings.DATABASE_URL_POSTGRES)
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
print("OAuth2passwordBearer : ", oauth2_scheme)       
