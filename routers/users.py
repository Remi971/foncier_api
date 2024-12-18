from fastapi import APIRouter, Body, Path, Depends, HTTPException
from sqlalchemy.orm import Session
from schema.users import Users, User_update
from services.user import create_user, update_user, delete_user, get_user, get_current_user
from dependencies import get_pg_db
router = APIRouter(
    prefix="/users"
)

@router.post("/")
def create(body: Users = Body, db: Session = Depends(get_pg_db)):
    return create_user(body, db)

@router.put("/{id}")
def update(
    id: str = Path, 
    body: User_update = Body,
    db: Session = Depends(get_pg_db)):
    return update_user(id, body, db)

@router.get("/{id}")
def get(id : str = Path, db: Session = Depends(get_pg_db)):
    return get_user(id, db)
   
    
@router.delete("/{id}")
def delete(id: str = Path, db : Session = Depends(get_pg_db)):
    return delete_user(id, db)

@router.get("/me", response_model=Users)
def get_my_profile(user: Users = Depends(get_current_user)):
    return user