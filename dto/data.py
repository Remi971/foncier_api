from enum import Enum

class LayerName(Enum):
    def __str__(self):
        return str(self.value)
    COMMUNE= "commune_id"
    COMMUNE_INFO = "commune_info"
    ENVELOPPE_INFO = "enveloppe_info"
    POTENTIEL_INFO = "potentiel_info"
    BATIMENT = "batiment_id"
    PARCELLE = "parcelle_id"
    TSURF = "tsurf_id"
    VOIEP = "voiep_id"
    ENVELOPPE = "enveloppe"
    POTENTIEL = "potentiel"
    