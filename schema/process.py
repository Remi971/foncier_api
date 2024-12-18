from pydantic import BaseModel
    
class PotentielLayer(BaseModel):
    id =int
    insee = str
    userId = int
    createdAt = str
    updatedAt = str
    geom = bytes