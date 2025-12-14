from pydantic import BaseModel, EmailStr, Field
import re

USERNAME_REGEX = r"^[a-zA-Z0-9_]{3,20}$"

class UserCreate(BaseModel):
    username: str = Field(..., regex=USERNAME_REGEX)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)

class UserLogin(BaseModel):
    username: str   
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr

    class Config:
        orm_mode = True
