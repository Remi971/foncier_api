from fastapi import APIRouter, Body, Path, Depends, HTTPException
from sqlalchemy.orm import Session
from schema.users import Users, User_update
from services.user import create_user, update_user, delete_user, get_user, get_current_user, get_all_users
from dependencies import get_pg_db, oauth2_scheme
from services.auth import credentials

router = APIRouter(
    prefix="/users"
)

@router.get("/", tags=["User"], summary="Get All Users")
def get_all(db: Session = Depends(get_pg_db), token: str = Depends(oauth2_scheme)):
    token_data = credentials(token)
    return get_all_users(db)

@router.put("/{id}", tags=["User"], summary="Update User")
def update(
    id: str = Path, 
    body: User_update = Body,
    db: Session = Depends(get_pg_db),
    token: str = Depends(oauth2_scheme)
    ):
    token_data = credentials(token)
    return update_user(token_data.id, body, db)

@router.get("/me", tags=["User"], summary="Get My Profile")
def get_my_profile(db: Session = Depends(get_pg_db), token: str = Depends(oauth2_scheme)):
    token_data = credentials(token)
    return get_current_user(db, token_data.email)

@router.get("/{id}", tags=["User"], summary="Get One User")
def get(id : str = Path, db: Session = Depends(get_pg_db), token: str = Depends(oauth2_scheme)):
    token_data = credentials(token)
    return get_user(id, db)
   
    
@router.delete("/{id}", tags=["User"], summary="Delete One User")
def delete(id: str = Path, db : Session = Depends(get_pg_db), token: str = Depends(oauth2_scheme)):
    token_data = credentials(token)
    return delete_user(id, db)
