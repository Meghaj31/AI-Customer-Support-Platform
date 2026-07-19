from pydantic import BaseModel,EmailStr
from uuid import UUID

class CompanyRegister(BaseModel):
    name:str
    email:EmailStr
    password:str

class CompanyLogin(BaseModel):
    email:EmailStr
    password:str

class CompanyResponse(BaseModel):
    id:UUID
    name:str
    email:str

    class Config:
        from_attributes=True

class TokenResponse(BaseModel):
    access_token:str
    token_type:str