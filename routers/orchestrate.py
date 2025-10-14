from fastapi import APIRouter, Body, Depends, HTTPException, status
from dependencies import EngineDb, oauth2_scheme, env
from services.auth import credentials
from dto.database import DatabaseTypeEnum
from schema.process import ProcessSchema
import httpx

router = APIRouter(
    prefix="/orchestrate"
)

database = EngineDb(DatabaseTypeEnum.POSTGRESQL)

@router.post('/', tags=['Orchestrate'], summary="Call the orchestration Microservice to handle data and processing subject")
def orchestrate(
    token: str = Depends(oauth2_scheme), 
    body: ProcessSchema = Body):
    token_data = credentials(token)
    # Use external service = Orchestration Microservice to handle
    try:
        httpx.post(
                f"{env.ORCHESTRATION_URL}/orchestrate",
                json=body
            )
        return {"mesage": f"Operation : {body.type} in progress"}
    except Exception as error:
        print("Error : ", error)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{error}")