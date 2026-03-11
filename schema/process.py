from pydantic import BaseModel, ConfigDict
from dto.process import PotentielParamsDto, EnveloppeParamsDto, CommuneDto, ProcessType
    
class PotentielLayer(BaseModel):
    id : int
    insee : str
    userId : int
    createdAt : str
    updatedAt : str
    geom : bytes
    
class ProcessSchema(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    type: ProcessType
    parameters: PotentielParamsDto | EnveloppeParamsDto | CommuneDto
    def __setattr__(self, name, value):
        return super().__setattr__(name, value)