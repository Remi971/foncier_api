from fastapi import APIRouter, Depends, status, HTTPException, Body, Path
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from services.data import get_data_enveloppe, get_data_commune, delete_data_enveloppe, save_data_enveloppe, clean_data, download_potentiel_layer
from services.auth import credentials
from services.orchestration import save_data
from dependencies import oauth2_scheme
from dto.process import DataFormat
from sqlalchemy.orm import Session
from dependencies import EngineDb
from dto.database import DatabaseTypeEnum
from custom_exception import ExceptionNotFound
import json

router = APIRouter(
    prefix="/data"
)

database = EngineDb(DatabaseTypeEnum.POSTGRESQL)

@router.get('/commune', tags=['Data'], summary="Check if commune data present in bucket")
def checkDataCommune(
    token: str = Depends(oauth2_scheme)
) -> JSONResponse:
    try:
        token_data = credentials(token)
        # get commune information from bucket
        return get_data_commune(token_data.id, database.engine)
    except ExceptionNotFound as error:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail=f"{error}")
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{error}")

@router.get('/enveloppe/{code}', tags=["Data"], summary="Get info about enveloppe data and the geojson layer")
def checkDataEnveloppe(
    token: str = Depends(oauth2_scheme),
    code: str = Path(...)
) -> JSONResponse:
    try:
        token_data = credentials(token)
        # get Enveloppe générée par l'utilisateur ID
        enveloppe_data = get_data_enveloppe(token_data.id, code, database.engine)
        info = {}
        if len(enveloppe_data["features"]):
            for key in enveloppe_data["features"][0]["properties"].keys():
                if key not in ['user']:
                    info[key] = enveloppe_data["features"][0]["properties"][key]
            content = {'info': info, 'data': enveloppe_data}
            return JSONResponse(content=jsonable_encoder(content))
        else:
            # raise ExceptionNotFound(name="enveloppe")
            raise ExceptionNotFound("The user don't have any enveloppe created yet.")
    except ExceptionNotFound as error:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail=f"{error}")
    except Exception as error:
        print(f"Error fetching enveloppe data : {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{error}")

@router.post('/save/enveloppe', tags=['Data'], summary='Save enveloppe layer in database')
def save_enveloppe(
    token: str = Depends(oauth2_scheme),
    body = Body(),
    db: Session = Depends(database.get_db)
) -> JSONResponse:
    try:
        token_data = credentials(token)
        print("body : ", body)
        print("body type : ", type(body))
        #TODO: Remove the row in database where user = token_data.id and code_insee = body.data['features'][0]['properties']['code_insee'] and type = 'enveloppe'
        
        delete_data_enveloppe(token_data.id, body['features'][0]['properties']['code'], database.engine)
        save_data_enveloppe(body, database.engine)
        return body
    except Exception as error:
        print(f"Error saving enveloppe data : {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{error}")

@router.post('/save/potentiel', tags=['Data'], summary='Save potentiel layer in database')
def save_potentiel(
    token: str = Depends(oauth2_scheme),
    body: DataFormat = Body(),
    db: Session = Depends(database.get_db)
) -> JSONResponse:
    try:
        ...
    except Exception as error:
        print(f"Error saving potentiel data : {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{error}")

    