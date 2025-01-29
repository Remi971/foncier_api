import geopandas as gpd
import pandas as pd
import requests
from zipfile import ZipFile
import os
from fastapi import HTTPException, status
import tarfile
from shutil import rmtree
from script.pyogr.ogr2ogr import main as ogr2ogr
from services.notifications import Notifiyer
from sqlalchemy.orm import Session
from dto.notifications import NotificationsState, NotificationsStatusEnum, NotificationsTypeEnum
from schema.notifications import Notifications
from sqlite3 import OperationalError
from sqlalchemy import inspect, text
from dependencies import engine
from util.layers import layers
from schema.data import CommuneDto
from models.data import CommuneInfo

def multi_to_single_polygon(gdf:gpd.GeoDataFrame):
    gdf_singlepoly: gpd.GeoSeries = gdf[gdf.geometry.type == 'Polygon']
    gdf_multipoly: gpd.GeoSeries = gdf[gdf.geometry.type == 'MultoPolygon']
    
    for i, row in gdf_multipoly.iterrows():
        series_geometries = pd.Series(row.geometry)
        df = pd.concat([gpd.GeoDataFrame(row, crs="EPSG:2154").T]*len(series_geometries), ignore_index=True)
        df['geometry'] = series_geometries
        gdf_singlepoly = pd.concat([gdf_singlepoly, df])
    gdf_singlepoly.reset_index(inplace=True, drop=True)
    return gdf_singlepoly

def get_data(body: CommuneDto, notifId: str, dbpg: Session, db: Session):
    data_url = f"https://cadastre.data.gouv.fr/bundler/pci-vecteur/communes/{body.code}/edigeo"
    try:
        clean_data(db)
        new_commune = CommuneInfo(
           name = body.nom,
           code = body.code ,
           lat = body.center.coordinates[0],
           long = body.center.coordinates[1]
        ) 
        db.add(new_commune)
        db.commit()
        if os.path.isfile("tmp/db.sqlite"):
            os.remove("tmp/db.sqlite")
        response = requests.get(data_url)
        response.raise_for_status()
        tmp_data = os.path.abspath(f'tmp/{body.code}.zip')
        with open(tmp_data, "wb") as f:
            f.write(response.content)
        with ZipFile(f"tmp/{body.code}.zip") as f:
            f.extractall('tmp')
        os.remove(f"tmp/{body.code}.zip")
        # extract all bz2
        for bz2 in os.listdir(f"tmp/{body.code}"):
            if bz2.split('.')[0] not in os.listdir(f"tmp/{body.code}"):
                try:
                    file = tarfile.open(f"tmp/{body.code}/{bz2}", 'r:bz2')
                    file.extractall("tmp/unzip")
                    file.close()
                except Exception as error:
                    raise HTTPException(status_code=500, detail=f"Failed unzip files : {error}")
        # remove all bz2
        rmtree(f"tmp/{body.code}")
        # Import EDIGEO
        thfList = []
        
        for dirpath, dirnames, filenames in os.walk('tmp'):
            filenames_fullpath = list(map(lambda file: os.path.join(dirpath, file), filenames))
            thfList = list(filter(lambda file: file.endswith('.THF'), filenames_fullpath))
        importEdigeoTHF(thfList)
        # for file in os.listdir('tmp'):
        rmtree('tmp/unzip')
        newNotif : Notifications = {
            "message": "Acquisition des données terminée",
            "status": NotificationsStatusEnum.SUCCESS,
            "type": NotificationsTypeEnum.DATA
        }
        notification = Notifiyer(state=NotificationsState.UPDATE, db=dbpg, notif=newNotif, id=notifId )
    except Exception as error:
        newNotif : Notifications = {
            "message": "L'acquisition des données a échoué",
            "status": NotificationsStatusEnum.ERROR,
            "type": NotificationsTypeEnum.DATA
        }
        errorNotification = Notifiyer(state=NotificationsState.UPDATE, db=dbpg, notif=newNotif, id=notifId)
        errorNotification.action()
        raise HTTPException(status_code=500, detail=f"Error : {error}")
    id = notification.action()
    
    print("Acquisition des données terminée ! ")
    return {"message": "Data downloaded and stored in database successfully !", "data": {"id": id}}


        
def importEdigeoTHF(thf_list):
    for thf in thf_list:
        print("Check THF : ", thf)
        cmdArgs = [
                '',
                '-s_srs', 'EPSG:2154',
                '-a_srs', 'EPSG:2154',
                '-append',
                '-f', 'SQLite',
                os.path.abspath('db.sqlite'),
                os.path.normpath(thf),
                '-lco', 'GEOMETRY_NAME=geom',
                '-nlt', 'GEOMETRY',
                '-dsco', 'SPATIALITE=YES',
                '-gt', '50000',
                '--config', 'OGR_EDIGEO_CREATE_LABEL_LAYERS', 'NO',
                '--config', 'OGR_SQLITE_SYNCHRONOUS', 'OFF',
                '--config', 'OGR_SQLITE_CACHE', '512'
            ]
        ogr2ogr(cmdArgs)
        
def check_data(db:Session) :
    try:
        query = "SELECT tex2 FROM commune_id LIMIT 1"
        commune_query = db.execute(text(query))
        commune_mapping = commune_query.mappings().all()
        return commune_mapping[0].tex2
    except Exception as error:
        if "no such table" in f"{error}":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{error}")
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{error}")
        
def clean_data(db:Session):
    try:
        inspector = inspect(engine)
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