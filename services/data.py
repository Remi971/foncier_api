import geopandas as gpd
import pandas as pd
import requests
from zipfile import ZipFile
import os
from fastapi import HTTPException
import tarfile
from shutil import rmtree
from script.pyogr.ogr2ogr import main as ogr2ogr

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

def get_data(insee: str):
    data_url = f"https://cadastre.data.gouv.fr/bundler/pci-vecteur/communes/{insee}/edigeo"
    try:
        response = requests.get(data_url)
        response.raise_for_status()
        tmp_data = os.path.abspath(f'tmp/{insee}.zip')
        with open(tmp_data, "wb") as f:
            f.write(response.content)
        with ZipFile(f"tmp/{insee}.zip") as f:
            f.extractall('tmp')
        os.remove(f"tmp/{insee}.zip")
        # extract all bz2
        for bz2 in os.listdir(f"tmp/{insee}"):
            if bz2.split('.')[0] not in os.listdir(f"tmp/{insee}"):
                try:
                    file = tarfile.open(f"tmp/{insee}/{bz2}", 'r:bz2')
                    file.extractall("tmp/unzip")
                    file.close()
                except Exception as error:
                    raise HTTPException(status_code=500, detail=f"Failed unzip files : {error}")
        # remove all bz2
        rmtree(f"tmp/{insee}")
        # Import EDIGEO
        thfList = []
        
        for dirpath, dirnames, filenames in os.walk('tmp'):
            filenames_fullpath = list(map(lambda file: os.path.join(dirpath, file), filenames))
            thfList = list(filter(lambda file: file.endswith('.THF'), filenames_fullpath))
        importEdigeoTHF(thfList)
        for file in os.listdir('tmp'):
            rmtree('tmp/unzip')
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Error : {error}")
    return "Data downloaded and stored in database successfully !"
        
def importEdigeoTHF(thf_list):
    for thf in thf_list:
        print("Check THF : ", thf)
        cmdArgs = [
                '',
                '-s_srs', 'EPSG:2154',
                '-a_srs', 'EPSG:2154',
                '-append',
                '-f', 'SQLite',
                os.path.abspath('tmp/db.sqlite'),
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
        
    