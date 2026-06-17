from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import Base

class Conversation(Base):
    __tablename__="conversations"

    id=Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id=Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    created_at=Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")