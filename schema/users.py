from pydantic import BaseModel, EmailStr
from typing import Optional
from dto.users import Roles

class User_update(BaseModel):
    firstname : str
    lastname : str
    
class Users_create(User_update):
    email : EmailStr
    password: str
    
class Users(Users_create):
    role : Optional[Roles] = Roles.BASIC