from pydantic import BaseModel

class PotentielParamsDto(BaseModel):
    minSurfParNue: int # Surface minimale de la parcelle non bâtie
    minSurfParBatie: int # Surface minimale de la parcelle bâtie
    maxCes: int # CES maximum de la parcelle bâtie
    minSurfDivision: int # Surface minimale du résultat de la division parcellaire
    distBufferTest: int # Distance du buffer pour le test
    distBufferBati: int # Distance du buffer autour du bâti
    createdAt: str
    updatedAt: str
    
class EnveloppeParamsDto(BaseModel):
    minSurfBati: int # Surface minimale du Bâti
    bufferBati: int # Buffer autour du bâti
    dilatation: int # Distance Buffer pour la dilatation
    erosion: int # Distance Buffer pour l'érosion
    minPartInBuffer: int # Part minimale de la parcelle comprise dans le buffer dilation-erosion
    maxSurfTrou: int # Surface maximale des trous à combler
    minSurfEnv: int # Surface minimale des enveloppes
    maxSurfResidus: int # Surface maximale des résidus à supprimer
    cretedAt: str
    updatedAt: str