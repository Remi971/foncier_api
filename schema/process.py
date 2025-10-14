from pydantic import BaseModel
from dto.process import PotentielParamsDto, EnveloppeParamsDto, CommuneDto, ProcessType
    
class PotentielLayer(BaseModel):
    id : int
    insee : str
    userId : int
    createdAt : str
    updatedAt : str
    geom : bytes
    
class ProcessSchema(BaseModel):
    type: ProcessType
    parameters: PotentielParamsDto | EnveloppeParamsDto | CommuneDto
    userId: str