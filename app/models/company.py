from sqlalchemy import Column,String,DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import Base

class Company(Base):
    __tablename__="companies"

    id=Column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    name=Column(String,nullable=False)
    email=Column(String,unique=True ,nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    documents=relationship("Document", back_populates="company")
    conversations = relationship("Conversation", back_populates="company")