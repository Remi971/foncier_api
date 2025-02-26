from geoalchemy2 import Geometry, Geography
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float
from dto.data import LayerName

Base = declarative_base()

class CommuneInfo(Base):
    __tablename__ = "commune_info"
    name = Column(String)
    code = Column(String, primary_key=True)
    lat = Column(Float)
    long = Column(Float)
    
class Enveloppe(Base):
    __tablename__ = "enveloppe"
    fid = Column(Integer, primary_key=True)
    geom = Column(Geometry(geometry_type="POLYGON", srid=2154, name="geom"))
    
class Potentiel(Base):
    __tablename__ = "potentiel"
    id = Column(Integer, primary_key=True)
    type = Column(String)
    color = Column(String)
    geom = Column(Geometry(geometry_type="POLYGON", srid=2154, name="geom"))
    
class EnveloppeInfo(Base):
    __tablename__ = "enveloppe_info"
    id = Column(Integer, primary_key=True)
    minSurfBati = Column(Integer)
    bufferBati = Column(Integer)
    dilatation = Column(Integer)
    erosion = Column(Integer)
    minPartInBuffer = Column(Integer)
    maxSurfTrou = Column(Integer)
    minSurfEnv = Column(Integer)
    maxSurfResidus = Column(Integer)
    
class PotentielInfo(Base):
    __tablename__ = "potentiel_info"
    id = Column(Integer, primary_key=True)
    minSurfParNue = Column(Integer)
    minSurfParBatie = Column(Integer)
    maxCes = Column(Integer)
    minSurfDivision = Column(Integer)
    distBufferTest = Column(Integer)
    distBufferBati = Column(Integer)