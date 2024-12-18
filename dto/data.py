from enum import Enum

class LayerName(Enum):
    def __str__(self):
        return str(self.value)
    COMMUNE= "commune_id"
    BATIMENT = "batiment_id"
    PARCELLE = "parcelle_id"
    TSURF = "tsurf_id"
    