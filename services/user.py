from fastapi import HTTPException, Depends, status
from schema.users import Users_create, User_update, Users
from models.users import User as user_model
from sqlalchemy.orm import Session
from dto.users import Roles
from sqlalchemy.exc import DataError
from datetime import datetime
from services.auth import get_password_hash, verify_password, credentials, oauth2_scheme


def create_user(body: Users_create, db: Session):
    try:
        newUser = body.model_dump()
        print(newUser)
        new_user = user_model(
            firstname=newUser["firstname"], 
            lastname=newUser["lastname"], 
            email=newUser["email"], 
            hashed_password=get_password_hash(newUser["password"]),
            role=Roles.BASIC.value,
            )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{error}")
    
def authenticate_user(db, username: str, password: str) -> Users:
    user = get_user_by_email(db, username)
    print("authenticate_user", user)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def get_current_user(db, email) -> Users:
    try:
        user = get_user_by_email(db, email=email)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
    
def get_user(id: str, db: Session):
    try:
        user = db.query(user_model).get({"id":id})
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found !")
        return user
    except DataError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"invalid input syntax for type uuid: {id}")
        
def get_all_users(db: Session):
    try:
        users = db.query(user_model).all()   
        return users
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{error}")   

def get_user_by_email(db, email: str) -> Users:
    print("email", email) 
    user = db.query(user_model).filter(user_model.email == email).all()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    try:
        return user[0]
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{error}")

def update_user(id:str, body: User_update, db):
    newUser = body.model_dump()
    print("newUser", newUser)
    user = db.query(user_model).get({"id": id})
    if not user:
        raise HTTPException(status_code=404, detail=f"User not found !")
    user.firstname = newUser["firstname"]
    user.lastname = newUser["lastname"]
    db.commit()
    return user
    
    
def delete_user(id: str, db):
    try:
        db.query(user_model).filter(user_model.id == id).delete()
        db.commit()
        return "User deleted"
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"{error}") 