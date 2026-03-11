from pydantic import BaseModel
from typing import List
class CenterDto(BaseModel):
    type: str
    coordinates: List[float]
class CommuneDto(BaseModel):
    nom: str
    code: str
    centre: CenterDto
