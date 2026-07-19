from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from app.models.message import RoleEnum

class MessageCreate(BaseModel):
    content:str

class MessageResponse(BaseModel):
    id:UUID
    role: RoleEnum
    content:str
    created_at:datetime
    escalated:bool

    class Config:
        from_attributes=True

class ConversationResponse(BaseModel):
    id:UUID
    created_at:datetime

    class Config:
        from_attributes=True
