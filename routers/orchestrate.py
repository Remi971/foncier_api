from fastapi import APIRouter, Body, Depends, HTTPException, status
from dependencies import EngineDb, oauth2_scheme, env
from services.auth import credentials
from dto.database import DatabaseTypeEnum
from schema.process import ProcessSchema
import httpx
from publisher import Publisher

router = APIRouter(
    prefix="/orchestrate"
)

database = EngineDb(DatabaseTypeEnum.POSTGRESQL)

# publisher = Publisher()

@router.post('/', tags=['Orchestrate'], summary="Call the orchestration Microservice to handle data and processing subject")
def orchestrate(
    token: str = Depends(oauth2_scheme), 
    body: ProcessSchema = Body,
    publisher=Depends(Publisher)):
    token_data = credentials(token)
    # Use external service = Orchestration Microservice to handle
    newBody = body.model_dump()
    newBody["userId"] = token_data.id
    print("Orchestrate body : ", newBody)
    try:
        publisher.publish_event(
            "data:processing", {
                "type": newBody["type"], 
                "status": "STARTED", 
                "message": f"{newBody['type']} started"
                })
        httpx.post(
                f"{env.ORCHESTRATION_URL}/orchestrate",
                json=newBody
            )
        return {"mesage": f"Operation : {newBody["type"]} in progress"}
    except Exception as error:
        print("Error : ", error)
        publisher.publish_event(
            "data:processing", {
                "type": newBody["type"], 
                "status": "FAILED", 
                "message": f"{newBody['type']} failed"
                })
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{error}")