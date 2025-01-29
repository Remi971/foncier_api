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
    geometry = Column(Geometry(geometry_type="POLYGON", srid=2154, name="geometry"))

# class Batiment(Base):
#     __tablename__ = LayerName.BATIMENT
#     ogc_fid = Column(Integer, primary_key=True)
#     object_rid = Column(String)
#     dur = Column(String)
#     tex = Column(String)
#     creat_date = Column(Integer)
#     update_date = Column(Integer)
#     geom = Column(Geometry)
    
# class Parcelle(Base):
#     __tablename__ = LayerName.PARCELLE.value
#     ogc_fid= Column(Integer, primary_key=True)
#     object_rid = Column(String)
#     idu = Column(String)
#     indp = Column(String)
#     geom = Column(Geometry)
 
# class Commune(Base):
#     __tablename__ = LayerName.COMMUNE.value
#     ogc_fid = Column(Integer, primary_key=True)
#     object_fid = Column(String)
#     idu = Column(String)
#     tex2 = Column(String)
#     creat_date = Column(Integer)
#     update_date = Column(Integer)
#     geom = Column(Geometry)
     
# class Tsurf(Base):
#     __tablename__ = LayerName.TSURF.value
#     ogc_fid = Column(Integer, primary_key=True)
#     object_fid = Column(String)
#     sym = Column(String)
#     tex = Column(String)
#     creat_date = Column(Integer)
#     update_date = Column(Integer)
#     geom = Column(Geometry)