from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.encoders import jsonable_encoder
import geopandas as gpd
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import Engine, delete
from sqlalchemy import inspect, text
from dependencies import EngineDb
from util.layers import layers
from models import Enveloppe, Commune
from .geoprocessing import Layer, LayerName
import json
import io
from custom_exception import ExceptionNotFound
        
def check_data_commune() :
    try:
        commune = Layer(LayerName.COMMUNE.value, EngineDb.engine)
        commune_info = Layer(LayerName.COMMUNE_INFO.value, EngineDb.engine)
        return {"data": commune.to_geojson(), "info": commune_info.getInfo()}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{error}")

def get_data_commune(userId: str, engine: Engine) -> JSONResponse: 
    session = Session(engine)
    lastCommune  = session.query(Commune).filter(Commune.userId == userId).order_by(Commune.created_at.desc()).first()
    if lastCommune:
        data = {
            "nom": lastCommune.nom,
            "code": lastCommune.code,
            "centre": {
                "type": "Point",
                "coordinates": [lastCommune.long, lastCommune.lat]
                }
            }
        return JSONResponse(content=jsonable_encoder(data))
    else:
        raise ExceptionNotFound("No commune data found for this user.")
    
def get_data_enveloppe(userId: str, code: str, engine: Engine) :
    try:
        sql = f"SELECT * FROM enveloppe WHERE enveloppe.user='{userId}' AND enveloppe.code='{code}';"
        gdf = gpd.GeoDataFrame.from_postgis(sql, engine)
        geojson = gdf.to_geo_dict()
        print("CRS : ", gdf.crs)
        return geojson
        # enveloppe = Layer(LayerName.ENVELOPPE.value, EngineDb.engine)
        # enveloppe_info = Layer(LayerName.ENVELOPPE_INFO.value, EngineDb.engine)
        # return {"data": enveloppe.to_geojson(), "info": enveloppe_info.getInfo()}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{error}")
    
def save_data_enveloppe(enveloppe: dict, engine: Engine):
    try:
        crs = {'init': 'epsg:4326'}
        gdf = gpd.GeoDataFrame.from_features(enveloppe["features"], crs=crs)
        # gdf.crs = 3857
        # gdf.geometry = gdf.geometry.to_crs("EPSG:4326")
        gdf.rename_geometry('geom', inplace=True)
        columns_to_keep = ['geom', 'nom', 'code', 'minSurfBati', 'bufferBati', 'dilatation', 'maxSurfResidus', 'user', 'erosion', 'minPartInBuffer', 'maxSurfTrou', 'minSurfEnv']
        for column in gdf.columns:
            if column not in columns_to_keep:
                gdf.drop(column, axis=1, inplace=True)
        print("##### gdf columns : ", gdf.columns)
        gdf = gdf.explode()
        gdf.to_postgis("enveloppe", engine, if_exists='append')
    except Exception as error:
        print(f"Saving The Enveloppe failed with error : {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
def check_data_potentiel() :
    try:
        potentiel = Layer(LayerName.POTENTIEL.value, EngineDb.engine)
        potentiel_info = Layer(LayerName.POTENTIEL_INFO.value, EngineDb.engine)
        return {"data": potentiel.to_geojson(), "info": potentiel_info.getInfo()}
    except Exception as error:
        print(error)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{error}")
    
def download_potentiel_layer():
    try:
        potentiel = Layer(LayerName.POTENTIEL.value, EngineDb.engine)
        geojson = potentiel.to_geojson()
        geojson_str = json.dumps(geojson)
        geojson_stream = io.StringIO(geojson)
        return StreamingResponse(
            iter([geojson_stream.getvalue()]),
            media_type="application/json",
            headers={'Content-Disposition': "attachment; filename=potentiel.geojson"}
        )
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{error}")
     
def delete_data_enveloppe(userId: str, code_insee: str, engine: Engine):
    try:
        stmt = delete(Enveloppe).where(Enveloppe.user == userId and Enveloppe.code_insee == code_insee)
        # with engine.connect() as connection:
            # connection.execute(text(sql))
        with Session(engine) as session:
            session.execute(stmt)
            session.commit()
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{error}")
   
def clean_data(db:Session):
    try:
        inspector = inspect(EngineDb.engine)
        for table_name in inspector.get_table_names():
            if table_name in layers:
                query = f"DELETE FROM {table_name}"
                execute = db.execute(text(query))
                print("table_name : ", table_name)
        db.commit()
        db.execute(text("VACUUM"))
        return {"message", "Database has been cleaned."}
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'{error}')