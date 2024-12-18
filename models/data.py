from geoalchemy2 import Geometry
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from dto.data import LayerName

Base = declarative_base()

class Batiment(Base):
    __tablename__ = LayerName.BATIMENT
    ogc_fid = Column(Integer, primary_key=True)
    object_rid = Column(String)
    dur = Column(String)
    tex = Column(String)
    creat_date = Column(Integer)
    update_date = Column(Integer)
    geom = Column(Geometry)
    
class Parcelle(Base):
    __tablename__ = LayerName.PARCELLE
    ogc_fid= Column(Integer, primary_key=True)
    object_rid = Column(String)
    idu = Column(String)
    indp = Column(String)
    geom = Column(Geometry)
 
class Commune(Base):
    __tablename__ = LayerName.COMMUNE
    ogc_fid = Column(Integer, primary_key=True)
    object_fid = Column(String)
    idu = Column(String)
    tex2 = Column(String)
    creat_date = Column(Integer)
    update_date = Column(Integer)
    geom = Column(Geometry)
     
class Tsurf(Base):
    __tablename__ = LayerName.TSURF
    ogc_fid = Column(Integer, primary_key=True)
    object_fid = Column(String)
    sym = Column(String)
    tex = Column(String)
    creat_date = Column(Integer)
    update_date = Column(Integer)
    geom = Column(Geometry)