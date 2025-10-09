from zipfile import ZipFile
import os
import tarfile
import sqlite3
import re
from script.pyogr.ogr2ogr import main as ogr2ogr
from script.getmultipolygonfromvec import GetMultiPolygonFromVec
import geopandas as gpd
import pandas as pd

def main():
    thfList = []
    for dirpath, dirnames, filenames in os.walk('tmp/unzip'):
        filenames_fullpath = list(map(lambda file: os.path.join(dirpath, file), filenames))
        thfList = list(filter(lambda file: file.endswith('.THF'), filenames_fullpath))
    print(thfList)
    
    for thf in thfList:
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
    
    
    
if __name__ == "__main__":
    main()