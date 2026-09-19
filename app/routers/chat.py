from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.company import Company
from app.schemas.chat import MessageCreate, MessageResponse, ConversationResponse
from app.services.auth_service import get_current_company
from app.services.chat_service import (
    create_new_conversation,
    get_conversation_messages,
    process_message,
)
from app.repositories.chat_repo import get_conversations_by_company

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/conversations", response_model=ConversationResponse, status_code=201)
async def start_conversation(
    db: AsyncSession = Depends(get_db),
    current_company: Company = Depends(get_current_company),
):
    return await create_new_conversation(db, current_company.id)

@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_company: Company = Depends(get_current_company),
):
    return await get_conversations_by_company(db, current_company.id)

@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse, status_code=201)
async def send_message(
    conversation_id: str,
    message: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_company: Company = Depends(get_current_company),
):
    return await process_message(db, conversation_id, current_company.id, message.content)


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_company: Company = Depends(get_current_company),
):
    return await get_conversation_messages(db, conversation_id, current_company.id)

