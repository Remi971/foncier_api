from fastapi import APIRouter, Body, Path, Depends, HTTPException
from sqlalchemy.orm import Session
from schema.users import Users, User_update
from services.user import create_user, update_user, delete_user, get_user, get_current_user, get_all_users
from dependencies import EngineDb, oauth2_scheme
from services.auth import credentials
from dto.database import DatabaseTypeEnum

router = APIRouter(
    prefix="/users"
)


database = EngineDb(DatabaseTypeEnum.POSTGRESQL)


@router.get("/", tags=["User"], summary="Get All Users")
def get_all(db: Session = Depends(database.get_db), token: str = Depends(oauth2_scheme)):
    token_data = credentials(token)
    return get_all_users(db)

@router.put("/{id}", tags=["User"], summary="Update User")
def update(
    id: str = Path, 
    body: User_update = Body,
    db: Session = Depends(database.get_db),
    token: str = Depends(oauth2_scheme)
    ):
    token_data = credentials(token)
    return update_user(token_data.id, body, db)

@router.get("/me", tags=["User"], summary="Get My Profile")
def get_my_profile(db: Session = Depends(database.get_db), token: str = Depends(oauth2_scheme)):
    token_data = credentials(token)
    return get_current_user(db, token_data.email)

@router.get("/{id}", tags=["User"], summary="Get One User")
def get(id : str = Path, db: Session = Depends(database.get_db), token: str = Depends(oauth2_scheme)):
    token_data = credentials(token)
    return get_user(id, db)
   
    
@router.delete("/{id}", tags=["User"], summary="Delete One User")
def delete(id: str = Path, db : Session = Depends(database.get_db), token: str = Depends(oauth2_scheme)):
    token_data = credentials(token)
    return delete_user(id, db)

@router.post("/signin", tags=["User"], summary="Create User")
def create(body: Users = Body, db: Session = Depends(database.get_db)):
    user = None
    try:
        user = create_user(body, db)
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"User with email {body.email} already exists")
    if not user:
        raise HTTPException(status_code=400, detail="Error creating user")
    return user