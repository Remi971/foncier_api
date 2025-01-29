import geopandas as gpd
import pandas as pd
import shapely
from shapely.geometry import MultiPoint
from dto.process import EnveloppeParamsDto, PotentielParamsDto
from functools import reduce
from dto.data import LayerName
from sqlalchemy import Engine
from sqlalchemy.orm import Session
from geoalchemy2.shape import from_shape
from models.data import Enveloppe as model_enveloppe

class Layer:
    def __init__(self, name:LayerName, engine: Engine):
        self.name = name
        self.engine = engine
        self.gdf = self.getFromDatabase()
    
    def getFromDatabase(self):
        sql = ""
        if (self.name == LayerName.COMMUNE.value):
            sql = f"SELECT ST_AsText(ST_GeomFromWKB(ST_AsBinary(geom))) as geometry, * FROM {self.name} LIMIT 1;"
        else:
            sql = f"SELECT ST_AsText(ST_GeomFromWKB(ST_AsBinary(geom))) as geometry, * FROM {self.name};"
        df = pd.read_sql_query(sql, self.engine)
        df["geometry"] = gpd.GeoSeries.from_wkt(df["geometry"])
        return gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:2154")


def tryOverlay(input1: gpd.GeoDataFrame, input2: gpd.GeoDataFrame, how=None):
    try:
        output = gpd.GeoDataFrame.overlay(input1, input2, how=how, keep_geom_type=True)
    except shapely.errors.TopologicalError:
        input1 = input1[input1["geometry"].is_valid]
        input1 = input1[input1["geometry"].notnull()]
        input2 = input2[input2["geometry"].is_valid]
        input2 = input2[input2["geometry"].notnull()]
        output = gpd.GeoDataFrame.overlay(input1, input2, how=how)
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
    #bati_buf = bati_buf[["fid", "idu", "geometry"]]
    bati_buf = tryOverlay(parcellesBaties, bati_buf, how='intersection')#intersection entre les parcelles et le buffer bu bati
    bati_buf = bati_buf[bati_buf.idu_1 == bati_buf.idu_2] #Maintien des parties du buffer correspondant au bati sur la parcelle
    bati_buf.drop("idu_2", axis=1, inplace=True)
    #EMPRISE MOBILISABLE = Patatoïdes
    emprise = tryOverlay(parcellesBaties, bati_buf, how='difference')
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
    bati_buf_bbox = bati_buf.copy()
    bati_buf_bbox = bati_buf_bbox.dissolve(by='idu_1', as_index=False)
    bati_buf_bbox = bati_buf_bbox.explode()
    bati_buf_bbox.geometry = bati_buf_bbox.geometry.apply(lambda geom: MultiPoint(list(geom.exterior.coords)))
    bati_buf_bbox.geometry = bati_buf_bbox.geometry.apply(lambda geom: geom.minimum_rotated_rectangle)
    bati_buf_bbox = bati_buf_bbox[['idu_1', 'geometry']]
    intersection = tryOverlay(bati_buf_bbox, parcellesBaties, how='intersection') #intersection entre les parcelles et le bounding
    intersection = intersection[intersection.idu == intersection.idu_1] #Maintien des parties du BoundingBox correspondant au bâti de la parcelle
    intersection = intersection.explode()
    intersection = intersection.dissolve(by='idu_1') #regroupement des Bounding Box retenues par numéro de parcelle
    liste_id_inter = [i for i in intersection['idu']]
    parc = parcellesBaties.loc[parcellesBaties['idu'].isin(liste_id_inter)]
    difference = tryOverlay(parc, intersection, how='difference') #Difference entre les parcelles divisibles et le bounding box du bâti
    difference['geometry'] = difference.apply(lambda x: x.geometry.buffer(-5).buffer(5, cap_style=2, join_style=2), axis=1)
    difference = difference.explode()
    difference = difference[difference.geometry.area >=minSurfDivision]
    difference = difference[["idu", "geometry"]]
    inter = tryOverlay(difference, parcellesBaties.loc[parcellesBaties['idu'].isin([i for i in difference['idu']])], how='intersection')
    inter = inter[inter.idu_1 == inter.idu_2]
    inter = inter[inter.geometry.area >= minSurfDivision]
    inter.drop("idu_2", axis=1, inplace=True)
    if exclues is not None:
        exclues.loc[exclues["idu"].isin(liste_id_echec), "test_emprise"] = 'echec du test division parcellaire'
        return emprise, inter, exclues
    else:
        return emprise, inter
 
def processing_envelop(_bati: gpd.GeoDataFrame, parcelle: gpd.GeoDataFrame, tsurf: gpd.GeoDataFrame, commune: gpd.GeoDataFrame, params: EnveloppeParamsDto, db: Session):
    #TODO : Add consideration of equipment point layer, join it to parcelle and count it as bati (stade, piscine, etc)
    dilatation = params.dilatation
    bati = tryOverlay(_bati, tsurf, how="union")
    bati_dilatation = bati.copy()
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
    enveloppe.to_file("tmp/db.gpkg", mode="w", layer="enveloppe", driver="GPKG")
    # enveloppe.to_file("db.sqlite", mode="w", layer="enveloppe", driver="SQLite")
    for row in enveloppe.itertuples():
        new_row = model_enveloppe(
            fid = getattr(row, "fid"),
            geometry = from_shape(getattr(row, "geometry"))
        )
        db.add(new_row)
    db.commit()
        
    return enveloppe.to_json()
    
    
def processing_potentiel(bati: gpd.GeoDataFrame, enveloppe: gpd.GeoDataFrame, parcelle: gpd.GeoDataFrame, params: PotentielParamsDto):
    #TODO: Consider the equipment point layer, join it with parcelle and add it to the ces layer with a value of 100%
    #TODO : Select parcelle et bati dans enveloppe 
    selection_bati = bati.apply(lambda geom: intersects_geom(geom["geometry"], enveloppe["geometry"]), axis=1)
    bati_selection = bati.loc[pd.Series(data=selection_bati, index=selection_bati.index)]
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
    potentiel = tryOverlay(potentiel_dents_creuses, division_parcellaire, how="union")
    potentiel.to_file("tmp/db.gpkg", mode="w", layer="potentiel", driver="gpkg")