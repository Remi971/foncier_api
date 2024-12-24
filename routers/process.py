from fastapi import APIRouter, HTTPException, Body, Depends
from dto.process import  PotentielParamsDto
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from dependencies import get_db, get_engine
import geopandas as gpd
import pandas as pd
from services.process import envelop_creation, register_enveloppe, register_potentiel, potentiel_calcul
from dto.process import EnveloppeParamsDto
router = APIRouter(
    prefix="/process"
)

#TODO : user send inputs (enveloppe layer, or params for creating enveloppe layer) AND potentiel params

@router.post('/enveloppe', tags=["Processing"], summary="Register Envelop operation")
def register_process_enveloppe(body: EnveloppeParamsDto = Body):
    '''Register Processing enveloppe creation to PostGreSQL database from the user And lunch the process'''
    register_enveloppe()
    
@router.post('/potentiel', tags=["Processing"], summary="Register Potentiel Operation")
def register_process_potentiel(body: PotentielParamsDto = Body):
    '''Register Processing potentiel calcul and lunch the process'''
    register_potentiel()
    
@router.get('enveloppe/create/:id', tags=["Processing"], summary="Launch Envelop calculation")
def envelop_creation(id):
    envelop_creation(id)
    
@router.get('potentiel/calcul/:id', tags=["Processing"], summary="Launch Potentiel Calculation")
def potentiel_calcul(id):
    potentiel_calcul(id)

@router.post('/enveloppe', tags=["Processing"])
def processing(
    body: EnveloppeParamsDto = Body,
    engine: Session = Depends(get_engine),
    db: Session = Depends(get_db)
):
    try:
        envelop_creation(body)
        return "Enveloppe created successfully"
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"{error}")
    
