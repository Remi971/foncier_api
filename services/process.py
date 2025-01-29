from sqlalchemy.orm import Session
from dto.process import EnveloppeParamsDto, PotentielParamsDto
from dependencies import engine
from dto.data import LayerName
from .geoprocessing import Layer, processing_envelop, processing_potentiel

def envelop_creation(body: EnveloppeParamsDto, db: Session):
    #TODO: Get layers from db.sqlite (bati and parcelle) and convert them to gdf
    bati = Layer(name=LayerName.BATIMENT.value, engine=engine)
    print(bati)
    parcelle = Layer(name=LayerName.PARCELLE.value, engine=engine)
    tsurf = Layer(name=LayerName.TSURF.value, engine=engine)
    commune = Layer(name=LayerName.COMMUNE.value, engine=engine)
    
    envelop = processing_envelop(
        bati.gdf,
        parcelle.gdf,
        tsurf.gdf,
        commune.gdf,
        body,
        db
    )
    #TODO: Return a geojson of the envelop
    return {"message": "Success", "data": envelop}

def potentiel_calcul(
    body: PotentielParamsDto,
    db: Session,
    notifId: str
    ):
    #TODO : Return a geojson of the potentiel
    potentiel = processing_potentiel()
    ...