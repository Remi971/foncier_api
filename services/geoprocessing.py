from fastapi import HTTPException, status
import geopandas as gpd
import pandas as pd
import numpy as np
import shapely
from shapely.geometry import MultiPoint
from dto.process import EnveloppeParamsDto, PotentielParamsDto
from functools import reduce
from dto.data import LayerName
from sqlalchemy import Engine
from sqlalchemy.orm import Session
from geoalchemy2.shape import from_shape
from models_temp.data import Enveloppe as model_enveloppe, EnveloppeInfo as model_enveloppe_info, Potentiel as model_potentiel, PotentielInfo as model_potentiel_info
from schema.data import CommuneDto, CenterDto

class Layer:
    def __init__(self, name:LayerName, engine: Engine):
        self.name = name
        self.engine = engine
        self.gdf = self.getFromDatabase()
    
    def getFromDatabase(self):
        sql = ""
        if self.name in [LayerName.COMMUNE_INFO.value, LayerName.ENVELOPPE_INFO.value, LayerName.POTENTIEL_INFO.value]:
            sql = f"SELECT * FROM {self.name}"
            df = pd.read_sql_query(sql, self.engine)
            return gpd.GeoDataFrame(df)
        else:
            if (self.name == LayerName.COMMUNE.value):
                sql = f"SELECT ST_AsText(ST_GeomFromWKB(ST_AsBinary(geom))) as geometry, * FROM {self.name} LIMIT 1;"
            else:
                sql = f"SELECT ST_AsText(ST_GeomFromWKB(ST_AsBinary(geom))) as geometry, * FROM {self.name};"
            df = pd.read_sql_query(sql, self.engine)
            df["geometry"] = gpd.GeoSeries.from_wkt(df["geometry"])
            df = df.drop(columns="geom")
            return gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:2154")

    def getPotentiel(self):
        try:
            if self.name == LayerName.POTENTIEL.value:
                sql_parcelle = f"SELECT ST_AsText(ST_GeomFromWKB(ST_AsBinary((geom)))) as geometry, * FROM {self.name} WHERE type='Dent creuse';"
                df_parcelle = pd.read_sql_query(sql_parcelle, self.engine)
                sql_division = f"SELECT ST_AsText(ST_GeomFromWKB(ST_AsBinary((geom)))) as geometry, * FROM {self.name} WHERE type='Division parcellaire';"
                df_division = pd.read_sql_query(sql_division, self.engine)
                parcelle = gpd.GeoDataFrame(df_parcelle, geometry="geometry", crs="EPSG:2154")
                division = gpd.GeoDataFrame(df_division, geometry="geometry", crs="EPSG:2154")
                print("getPotentiel Function check : ", df_parcelle.columns)
                parcelle.to_file("tmp/db.gpkg", mode="w", layer="potentiel_parcelle", driver="GPKG")
                division.to_file("tmp/db.gpkg", mode="w", layer="potentiel_division", driver="GPKG")
                return {
                    "parcelle": parcelle,
                    "division": division
                    }
        except Exception as error:
            print(error)
    
    def getInfo(self):
        match(self.name):
            case LayerName.COMMUNE_INFO.value:
                commune = self.gdf
                info = CommuneDto(
                    nom= commune["name"][0],
                    code= commune["code"][0],
                    centre= CenterDto(
                        type= "POINT",
                        coordinates = [commune["lat"][0], commune["long"][0]]   
                    )
                )
                return info
            
            case LayerName.ENVELOPPE_INFO.value:
                enveloppe = self.gdf.head(1)
                info = EnveloppeParamsDto(
                    minSurfBati=enveloppe["minSurfBati"][0],
                    bufferBati=enveloppe["bufferBati"][0],
                    dilatation=enveloppe["dilatation"][0],
                    erosion=enveloppe["erosion"][0],
                    minPartInBuffer=enveloppe["minPartInBuffer"][0],
                    maxSurfTrou=enveloppe["maxSurfTrou"][0],
                    minSurfEnv=enveloppe["minSurfEnv"][0],
                    maxSurfResidus=enveloppe["maxSurfResidus"][0]
                )
                return info
            case LayerName.POTENTIEL_INFO.value:
                if len(self.gdf):
                    potentiel = self.gdf.head(1)
                    info = PotentielParamsDto(
                        minSurfParNue=potentiel["minSurfParNue"][0],
                        minSurfParBatie=potentiel["minSurfParBatie"][0],
                        maxCes=potentiel["maxCes"][0],
                        minSurfDivision=potentiel["minSurfDivision"][0],
                        distBufferTest=potentiel["distBufferTest"][0],
                        distBufferBati=potentiel["distBufferBati"][0]
                    )
                    return info
                else:
                    return None
    
    def to_geojson(self):
        if self.name == LayerName.POTENTIEL:
            potentiel = self.getPotentiel()
            parcelle = potentiel.parcelle
            division = potentiel.division
            parcelle = parcelle[parcelle["geometry"].is_valid()]
            division = division[division["geometry"].is_valid()]
            parcelle_reproj = parcelle.to_crs(4326)
            division_reproj = division.to_crs(4326)
            return {"parcelle": parcelle_reproj.to_json(), "division" : division_reproj.to_json()}
        elif len(self.gdf) and self.name != LayerName.POTENTIEL:
            reproj = self.gdf.to_crs(4326)
            return reproj.to_json()
        else: 
            return None


def tryOverlay(input1: gpd.GeoDataFrame, input2: gpd.GeoDataFrame, how=None):
    try:
        input1.geometry = input1.make_valid()
        input2.geometry = input2.make_valid()
        output = gpd.GeoDataFrame.overlay(input1, input2, how=how, keep_geom_type=True)
    except (shapely.errors.TopologicalError, shapely.errors.GEOSException) as error:
        input1 = input1[input1["geometry"].is_valid]
        input1 = input1[input1["geometry"].notnull()]
        input2 = input2[input2["geometry"].is_valid]
        input2 = input2[input2["geometry"].notnull()]
        output = gpd.GeoDataFrame.overlay(input1, input2, how=how, keep_geom_type=True)
        print(f"tryOverlay error : {error}")
    return output.explode()

def intersects_geom(geom, gdf_int: gpd.GeoSeries) -> bool:
    '''
    Function to add in a GeoDataFrame.apply() lambda function to check if geometry intersects at least one geometry of the GeoSeries
    '''
    for geom_int in gdf_int:
        if geom.centroid.intersects(geom_int):
            return True
    return False

def coeffEmpriseSol(bati: gpd.GeoDataFrame, parcelle: gpd.GeoDataFrame) -> gpd.GeoDataFrame :
    print("\n   ##   Calcul du CES   ##   \n")
    bati = bati.copy()
    parcelle = parcelle.copy()
    intersection = tryOverlay(parcelle, bati, how='intersection')
    if "idu" not in intersection.columns:
        intersection["idu"] = intersection["idu_1"]
    intersection.to_file("tmp/db.gpkg", mode="w", layer="intersection", driver="GPKG")
    dissolve = intersection.dissolve(by="idu").reset_index()
    dissolve.insert(len(dissolve.columns), "surf_bat", dissolve.geometry.area)
    dissolve.drop("geometry", axis=1, inplace=True)
    coeff = parcelle.merge(dissolve, how='left', on="idu", suffixes=('', '_y'))
    coeff.insert(len(coeff.columns), "surf_par", coeff.geometry.area)
    coeff['ces'] = coeff['surf_bat']/coeff['surf_par']*100
    coeff = coeff.fillna(0)
    for i in list(coeff.columns):
         if i not in ['idu','surf_par', 'surf_bat', 'ces', 'geometry']:
            coeff = coeff.drop(i, axis=1)
    coeff.crs = "EPSG:2154"
    return(coeff)

#Test des emprises mobilisables des parcelles non bâtie
def test_emprise_vide(parcelles: gpd.GeoDataFrame, dist_test: int, minSurfDivision: int, exclues: gpd.GeoDataFrame | None=None):
    print("\n   ## Test des parcelles vides   ##   \n")
    couche_buf = parcelles.copy()
    #Applique un buffer pour chaque entité suivant la valeur de minSurfDivision 
    couche_buf['geometry'] = couche_buf.apply(lambda x: x.geometry.buffer(-dist_test).buffer(dist_test), axis=1)
    couche_buf = couche_buf[couche_buf.geometry.area >= minSurfDivision]
    couche_buf["surf_par"] = couche_buf.geometry.area
    liste_id = [i for i in couche_buf['idu']]
    #selection = selection.loc[~selection['id_par'].isin(liste_id)]
    if exclues is not None:
        exclues.loc[~exclues["idu"].isin(liste_id), "test_emprise"] = 'echec du test dents creuses'
        return couche_buf, exclues
    else:
        return parcelles[parcelles["idu"].isin(liste_id)]
    
#Test des emprises mobilisables des parcelles bâtie
def test_emprise_batie(parcellesBaties, bati, distBufferBati, distBufferTest, minSurfDivision, exclues=None):
    print("\n   ## Test des parcelles baties   ##   \n")
    bati_buf = bati.copy()
    parcellesBaties.crs = "EPSG:2154"
    bati_buf.crs = "EPSG:2154"
    bati_buf = tryOverlay(parcellesBaties, bati_buf, how='intersection') #Découpage du bati par les parcelles baties
    #bati_buf = explode(bati_buf)
    bati_buf = bati_buf[bati_buf.geometry.area > 10] #Suppression des petits bouts (10m²)
    bati_buf['geometry'] = bati_buf.apply(lambda x: x.geometry.buffer(distBufferBati), axis=1) #buffer du bati d'après les paramètres
    bati_buf = tryOverlay(parcellesBaties, bati_buf, how='intersection')#intersection entre les parcelles et le buffer bu bati
    bati_buf = bati_buf[bati_buf.idu_1 == bati_buf.idu_2] #Maintien des parties du buffer correspondant au bati sur la parcelle
    bati_buf.drop("idu_2", axis=1, inplace=True)
    if "idu" not in bati_buf.columns:
        bati_buf["idu"] = bati_buf["idu_1"]
    bati_buf = bati_buf[["idu", "geometry"]]
    #EMPRISE MOBILISABLE = Patatoïdes
    bati_buf_dissolve = bati_buf.dissolve(by="idu", as_index=False)
    bati_buf_dissolve = bati_buf_dissolve.explode()
    
    emprise = tryOverlay(parcellesBaties, bati_buf_dissolve, how='difference')
    emprise = emprise.explode()
    emprise['geometry'] = emprise.apply(lambda x: x.geometry.buffer(-distBufferTest).buffer(distBufferTest), axis=1)
    #enregistrement des parcelles ne passant pas le test dans la couche exclues
    emprise_echec = emprise[emprise.geometry.area < minSurfDivision]
    liste_id_echec = [i for i in emprise_echec['idu']]
    #Maintien des parcelles passant le test avec succès dans la couche emprise
    emprise = emprise[emprise.geometry.area >= minSurfDivision]
    emprise["surf_par"] = emprise.geometry.area
    ##### METHODE DES BOUNDING BOX #####
    #BoundingBox du buffer du bâti
    bati_buf_bbox = bati_buf_dissolve.copy()
    bati_buf_bbox = bati_buf_bbox.dissolve(by='idu', as_index=False)
    bati_buf_bbox = bati_buf_bbox.explode()
    bati_buf_bbox.geometry = bati_buf_bbox.geometry.apply(lambda geom: MultiPoint(list(geom.exterior.coords)))
    bati_buf_bbox.geometry = bati_buf_bbox.geometry.apply(lambda geom: geom.minimum_rotated_rectangle)
    bati_buf_bbox = bati_buf_bbox[['idu', 'geometry']]
    intersection = tryOverlay(bati_buf_bbox, parcellesBaties, how='intersection') #intersection entre les parcelles et le bounding
    bati_buf_bbox.to_file("tmp/db.gpkg", mode="w", layer="bati_buf_bbox", driver="GPKG")
    intersection = intersection[intersection["idu_1"] == intersection["idu_2"]] #Maintien des parties du BoundingBox correspondant au bâti de la parcelle
    intersection = intersection.explode()
    intersection = intersection.dissolve(by='idu_1') #regroupement des Bounding Box retenues par numéro de parcelle
    intersection.to_file("tmp/db.gpkg", mode="w", layer="intersection2", driver="GPKG")
    if "idu" not in intersection.columns:
        intersection["idu"] = intersection["idu_2"]
    liste_id_inter = [i for i in intersection['idu']]
    parc = parcellesBaties.loc[parcellesBaties['idu'].isin(liste_id_inter)]
    difference = tryOverlay(parc, intersection, how='difference') #Difference entre les parcelles divisibles et le bounding box du bâti
    difference['geometry'] = difference.apply(lambda x: x.geometry.buffer(-5).buffer(5, cap_style=2, join_style=2), axis=1)
    difference = difference.explode()
    difference = difference[difference.geometry.area >=minSurfDivision]
    difference = difference[["idu", "geometry"]]
    inter = tryOverlay(difference, parcellesBaties.loc[parcellesBaties['idu'].isin([i for i in difference['idu']])], how='intersection')
    inter = inter[inter["idu_1"] == inter["idu_2"]]
    inter = inter[inter.geometry.area >= minSurfDivision]
    inter.drop("idu_2", axis=1, inplace=True)
    if exclues is not None:
        exclues.loc[exclues["idu"].isin(liste_id_echec), "test_emprise"] = 'echec du test division parcellaire'
        return emprise, inter, exclues
    else:
        return emprise, inter

def enveloppeParamsControl(params: EnveloppeParamsDto):
    errors = []
    if params.dilatation <= 0:
        errors.push("dilatation value must be greater than zero")
    if params.erosion > 0:
        errors.push("erosion value must be negative or equal to zero")
    if params.minSurfEnv < 0:
        errors.push("minSurfEnv value must be positive")
    if params.maxSurfTrou < 0:
        errors.push("maxSurfTrou value must be positive")
    return errors

def potentielParamsControl(params: PotentielParamsDto):
    errors = []
    if params.minSurfParNue <= 0:
        errors.push("minSurfParNue value must be greater than zero")
    if params.minSurfParBatie <= 0:
        errors.push("minSurfParBatie value must be greater than zero")
    if params.maxCes < 0 | params.maxCes > 100:
        errors.push("maxCes value must be positive and smaller or equal to 100")
    if params.minSurfDivision < 0:
        errors.push("minSurfDivision value must be positive")
    if params.distBufferTest < 0:
        errors.push("distBufferTest value must be positive")
    if params.distBufferBati < 0:
        errors.push("distBufferBati value must be positive")
    return errors
 
def processing_envelop(_bati: gpd.GeoDataFrame, parcelle: gpd.GeoDataFrame, tsurf: gpd.GeoDataFrame, commune: gpd.GeoDataFrame, voiep: gpd.GeoDataFrame, params: EnveloppeParamsDto, db: Session, notifId: str):
    try:
        #TODO : Add consideration of equipment point layer, join it to parcelle and count it as bati (stade, piscine, etc)
        dilatation = params.dilatation
        equipement = gpd.sjoin(parcelle, voiep, how='inner', predicate='contains')
        bati = tryOverlay(_bati, tsurf, how="union")
        bati_equip = tryOverlay(bati, equipement, how="union")
        bati_dilatation = bati_equip.copy()
        bati_dilatation["geometry"] = bati.buffer(dilatation)
        bati_dilatation.insert(1, 'diss', 1)
        bati_dilatation = bati_dilatation.dissolve("diss")
        #Erosion
        erosion = params.erosion
        minSurfEnv = params.minSurfEnv
        bati_erosion = bati_dilatation.copy()
        bati_erosion["geometry"] = bati_dilatation.buffer(erosion)
        bati_erosion = bati_erosion.explode()
        # Filtre des partie supérieure à minSurfEnv
        bati_erosion = bati_erosion[bati_erosion["geometry"].area > minSurfEnv]
        # bati_erosion.to_file("db.sqlite", engine="pyogrio", driver="SQLite", layer="enveloppe2", mode="a", spatialite=True)
        difference_env = tryOverlay(commune, bati_erosion, how="difference")
        env_area =  reduce(lambda prev, cur: prev + int(cur.area), bati_erosion["geometry"], 0)
        maxSurfTrou = params.maxSurfTrou
        difference_env = difference_env.loc[(difference_env["geometry"].area.astype('int') < env_area) & (difference_env["geometry"].area.astype('int') > maxSurfTrou)]
        difference_env["geometry"] = difference_env.buffer(1)
        enveloppe = tryOverlay(bati_erosion, difference_env, how="union")
        enveloppe.insert(1, "diss", 1)
        enveloppe = enveloppe.dissolve("diss").explode()
        enveloppe["fid"] = range(1, 1  + len(enveloppe))
        enveloppe = enveloppe[["fid", "geometry"]]
        return enveloppe
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"processing_enveloppe error: {error}")
    
def saveEnvelopInDb(enveloppe: gpd.GeoDataFrame, db: Session, params: EnveloppeParamsDto):
    try:
        for row in enveloppe.itertuples():
            new_row = model_enveloppe(
                fid = getattr(row, "fid"),
                geom = from_shape(getattr(row, "geometry"))
            )
            db.add(new_row)
        enveloppe_info = model_enveloppe_info(**params.model_dump())
        db.add(enveloppe_info)
        db.commit()
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"saveEnveloppeInDb error: {error}")
    
    
def processing_potentiel(bati: gpd.GeoDataFrame, enveloppe: gpd.GeoDataFrame, parcelle: gpd.GeoDataFrame, tsurf: gpd.GeoDataFrame, voiep: gpd.GeoDataFrame, params: PotentielParamsDto):
    try:
        equipement = gpd.sjoin(parcelle, voiep, how='inner', predicate='contains')
        _bati = tryOverlay(bati, tsurf, how="union")
        bati_equip = tryOverlay(_bati, equipement, how="union")
        selection_bati = bati_equip.apply(lambda geom: intersects_geom(geom["geometry"], enveloppe["geometry"]), axis=1)
        bati_selection = bati_equip.loc[pd.Series(data=selection_bati, index=selection_bati.index)]
        bati_selection.to_file("tmp/db.gpkg", mode="w", layer="bati", driver="GPKG")
        selection_parcelle = parcelle.apply(lambda geom: intersects_geom(geom["geometry"], enveloppe["geometry"]), axis=1)
        parcelle_selection = parcelle.loc[pd.Series(data=selection_parcelle, index=selection_parcelle.index)]
        parcelle_selection.to_file("tmp/db.gpkg", mode="w", layer="parcelle", driver="GPKG")
        #TODO calcul du CES
        ces = coeffEmpriseSol(bati_selection, parcelle_selection)
        ces.to_file("tmp/db.gpkg", mode="w", layer="ces", driver="GPKG")
        #TODO : première couche avec les parcelles non baties et le premier potentiel de parcelles divisibles
        minSurfParNue = params.minSurfParNue
        maxCes = params.maxCes
        minSurfParBatie = params.minSurfParBatie
        potentiel_brut = ces[(ces["ces"] < 0.5) & (ces.geometry.area >= minSurfParNue)| (ces["ces"] >= 0.5) & (ces["ces"] < maxCes) & (ces.geometry.area >= minSurfParBatie)]
        potentiel_brut.to_file("tmp/db.gpkg", mode="w", layer="potentiel_brut", driver="gpkg")
        #TODO : tester les parcelles non bâties et les divisions parcellaires
        distBufferTest = params.distBufferTest
        distBufferBati = params.distBufferBati
        minSurfDivision = params.minSurfDivision
        potentiel_dents_creuses = test_emprise_vide(potentiel_brut[potentiel_brut["ces"] < 0.5], distBufferTest, minSurfDivision)
        division_parcellaire, bounding_box = test_emprise_batie(potentiel_brut[potentiel_brut["ces"] >= 0.5], bati, distBufferBati, distBufferTest, minSurfDivision)
        potentiel_dents_creuses["type"] = "Dent creuse"
        potentiel_dents_creuses["color"] = "#f590d2"
        division_parcellaire["type"] = "Division parcellaire"
        division_parcellaire["color"] = "#f21b30"
        potentiel = tryOverlay(potentiel_dents_creuses, division_parcellaire, how="union")
        potentiel = potentiel[potentiel.geometry.area > 1]
        potentiel["type"] = np.where(potentiel["type_1"] == "Dent creuse", "Dent creuse", "Division parcellaire")
        potentiel["color"] = np.where(potentiel["color_1"] == "#f590d2", "#f590d2", "#f21b30")
        potentiel.to_file("tmp/db.gpkg", mode="w", layer="potentiel", driver="gpkg")
        return potentiel
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"processing_potentiel error : {error}")
    
def savePotentielInDb(potentiel: gpd.GeoDataFrame, db: Session, params: PotentielParamsDto):
    try:
        clean_potentiel = potentiel.copy()
        print(clean_potentiel.columns)
        clean_potentiel["geometry"] = clean_potentiel["geometry"].make_valid()
        clean_potentiel.to_file("tmp/db.gpkg", layer="clean_potentiel", mode="w", driver="gpkg")
        for row in clean_potentiel.itertuples():
            new_row = model_potentiel(
                type = getattr(row, "type"),
                color = getattr(row, 'color'),
                geom = from_shape(getattr(row, "geometry"))
            )
            db.add(new_row)
        potentiel_info = model_potentiel_info(**params.model_dump())
        db.add(potentiel_info)
        db.commit()
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"savePotentielInDb error: {error}")
    