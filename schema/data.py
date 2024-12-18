from pydantic import BaseModel
from geoalchemy2 import Geometry

class Batiment(BaseModel):
    ogc_fid : int
    object_rid : str
    dur : str
    tex : str
    creat_date : int
    update_date : int
    geom : Geometry
    
class Parcelle(BaseModel):
    ogc_fid: int
    object_rid : str
    idu : str
    indp : str
    geom : Geometry
 
class Commune(BaseModel):
    ogc_fid : int
    object_fid : str
    idu : str
    tex2 : str
    creat_date : int 
    update_date : int 
    geom : Geometry
     
class Tsurf(BaseModel):
    ogc_fid : int
    object_fid : str
    sym : str 
    tex : str 
    creat_date : int
    update_date : int
    geom : Geometry