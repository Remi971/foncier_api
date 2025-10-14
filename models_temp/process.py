from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, TIMESTAMP, text
from geoalchemy2 import Geometry

Base = declarative_base()

class Processing(Base):
    __tablename__= "processing"
    id = Column(Integer, nullable=False, primary_key=True)
    insee = Column(Integer, nullable=False)
    userId = Column(Integer, nullable=False)
    createdAt = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('Now()'))
    updatedAt = Column(TIMESTAMP(timezone=True), nullable=False, server_onupdate=text('Now()'))
    geom = Column(Geometry, nullable=False)